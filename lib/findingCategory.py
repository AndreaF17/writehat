import io
import re
import urllib.error
import urllib.request
import zipfile
import xml.etree.ElementTree as ET

from django.core.exceptions import ValidationError
from django.db import models
from django.db import transaction

from writehat.models import WriteHatBaseModel
from writehat.validation import allowed_for_names


DEFAULT_CWE_FEED_URL = 'https://cwe.mitre.org/data/xml/cwec_latest.xml.zip'


def _sanitize_category_name(name):
    sanitized = ''.join(ch if ch in allowed_for_names else ' ' for ch in str(name))
    sanitized = ' '.join(sanitized.split())
    return sanitized[:1000]


#This defines the categories that findings can belong to. This is an infinitely nestable class with a parent-child structure.
class DatabaseFindingCategory(WriteHatBaseModel):

    categoryParent = models.UUIDField(editable=False,null=True)

    def getCategoryBreadcrumbs(self):
        from writehat.lib.findingCategory import DatabaseFindingCategory
        breadcrumbs = []
        breadcrumbs.append(self.name)
        currentNode = self
        rootNode = DatabaseFindingCategory.getRootNode()
        while 1:
            #print(currentNode.categoryParent)
            if currentNode.categoryParent == rootNode.id:
                break
            else:
                parentNode = DatabaseFindingCategory.objects.get(id=currentNode.categoryParent)
                breadcrumbs.append(parentNode.name)
                currentNode = parentNode
        #print(breadcrumbs)
        return breadcrumbs


    @property
    def fullName(self):

        return ' -> '.join(self.getCategoryBreadcrumbs()[::-1])


    #@classmethod
    #def getRootNode(cls):
    #    return cls.objects.filter(categoryParent__isnull=True).first()

    @classmethod
    def getRootNode(cls):
        try:
            #intialize the growTree function with the root node
            rootNode = cls.objects.filter(categoryParent__isnull=True)[0]
        except IndexError:
            # We assume the database is brand new, so we will create the root node   
            rootNode = cls()
            rootNode.name = "root"
            rootNode.save()
        return rootNode


    @classmethod
    def getCategoriesFlat(cls):
        flatCategoryList = []
        #   rootNode = getRootNode()
        nonRootNodes = cls.objects.filter(categoryParent__isnull=False)
        #print(len(nonRootNodes))
        # For all the nodes that arent the root nodes
        for node in nonRootNodes:
            breadcrumbs = node.getCategoryBreadcrumbs()
            if len(breadcrumbs) > 0:
                flatCategoryList.append({'id':str(node.id),'name':' -> '.join(breadcrumbs[::-1])})
        return sorted(flatCategoryList, key=lambda k: k['name'])


    @classmethod
    def _load_cwe_xml(cls, uploaded_file):
        raw = uploaded_file.read()
        filename = str(getattr(uploaded_file, 'name', '')).lower()
        return cls._extract_cwe_xml(raw=raw, filename=filename, empty_error='Uploaded file is empty')


    @classmethod
    def _extract_cwe_xml(cls, raw, filename='', empty_error='No data was downloaded'):
        if not raw:
            raise ValueError(empty_error)

        looks_like_zip = filename.endswith('.zip') or raw[:4] == b'PK\x03\x04'

        if looks_like_zip:
            try:
                with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                    xml_members = sorted([m for m in archive.namelist() if m.lower().endswith('.xml')])
                    if not xml_members:
                        raise ValueError('CWE ZIP does not contain an XML file')
                    with archive.open(xml_members[0]) as xml_file:
                        return xml_file.read()
            except zipfile.BadZipFile:
                raise ValueError('Invalid ZIP file')

        return raw


    @classmethod
    def _download_cwe_xml(cls, url):
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                final_url = response.geturl()
                raw = response.read()
        except urllib.error.URLError as e:
            raise ValueError(f'Failed to download CWE feed: {e}')

        filename = final_url.rsplit('/', 1)[-1].lower()
        return cls._extract_cwe_xml(raw=raw, filename=filename)


    @classmethod
    def _parse_cwe_entries(cls, xml_bytes):
        try:
            root = ET.fromstring(xml_bytes)
        except ET.ParseError as e:
            raise ValueError(f'Invalid CWE XML: {e}')

        namespace = ''
        namespace_match = re.match(r'^\{([^}]+)\}', root.tag)
        if namespace_match:
            namespace = namespace_match.group(1)

        if namespace:
            ns = {'cwe': namespace}
            weaknesses = root.find('cwe:Weaknesses', ns)
            weakness_nodes = [] if weaknesses is None else weaknesses.findall('cwe:Weakness', ns)
        else:
            weaknesses = root.find('Weaknesses')
            weakness_nodes = [] if weaknesses is None else weaknesses.findall('Weakness')

        if weaknesses is None:
            raise ValueError('Could not find CWE Weaknesses section in XML file')

        entries = []
        seen_ids = set()

        for weakness in weakness_nodes:
            cwe_id = str(weakness.attrib.get('ID', '')).strip()
            cwe_name = str(weakness.attrib.get('Name', '')).strip()
            cwe_status = str(weakness.attrib.get('Status', '')).strip().lower()

            if not cwe_id.isdigit() or not cwe_name:
                continue

            if cwe_status in ('deprecated', 'obsolete'):
                continue

            if cwe_id in seen_ids:
                continue

            seen_ids.add(cwe_id)
            entries.append((cwe_id, cwe_name))

        if not entries:
            raise ValueError('No importable CWE entries were found in the XML file')

        return sorted(entries, key=lambda x: int(x[0]))


    @classmethod
    def import_cwe_categories(cls, uploaded_file):
        xml_bytes = cls._load_cwe_xml(uploaded_file)
        return cls.import_cwe_categories_from_xml(xml_bytes)


    @classmethod
    def import_cwe_categories_remote(cls):
        xml_bytes = cls._download_cwe_xml(DEFAULT_CWE_FEED_URL)
        return cls.import_cwe_categories_from_xml(xml_bytes)


    @classmethod
    def import_cwe_categories_from_xml(cls, xml_bytes):
        entries = cls._parse_cwe_entries(xml_bytes)

        root_node = cls.getRootNode()
        cwe_root_name = _sanitize_category_name('CWE')

        with transaction.atomic():
            cwe_parent = cls.objects.filter(categoryParent=root_node.id, name=cwe_root_name).first()
            if cwe_parent is None:
                cwe_parent = cls(name=cwe_root_name, categoryParent=root_node.id)
                cwe_parent.full_clean()
                cwe_parent.save()

            existing_ids = set()
            cwe_id_pattern = re.compile(r'^CWE-(\d+):')
            for category in cls.objects.filter(categoryParent=cwe_parent.id):
                match = cwe_id_pattern.match(str(category.name))
                if match:
                    existing_ids.add(match.group(1))

            created = 0
            skipped = 0
            invalid = 0

            for cwe_id, cwe_name in entries:
                if cwe_id in existing_ids:
                    skipped += 1
                    continue

                category_name = _sanitize_category_name(f'CWE-{cwe_id}: {cwe_name}')
                if not category_name:
                    invalid += 1
                    continue

                category = cls(name=category_name, categoryParent=cwe_parent.id)
                try:
                    category.full_clean()
                    category.save()
                    created += 1
                    existing_ids.add(cwe_id)
                except ValidationError:
                    invalid += 1

            # Update modifiedDate to represent the most recent sync attempt.
            cwe_parent.save()

        return {
            'created': created,
            'skipped': skipped,
            'invalid': invalid,
            'total': len(entries),
            'parentCategory': str(cwe_parent.id),
            'lastSynced': cwe_parent.modifiedDate.isoformat(),
        }
