import os
import pymongo
import importlib
import importlib.util
import sys
from pathlib import Path
from writehat.lib.errors import *
from writehat.validation import isValidStrictName


# read writehat config
import toml
writehat_config_file = Path(__file__).parent.parent / 'config/writehat.conf'
writehat_config = toml.load(str(writehat_config_file))


def _get_custom_component_roots():
    custom_component_roots = []

    custom_config = writehat_config.get('custom_components', {})
    config_paths = custom_config.get('paths', [])
    if isinstance(config_paths, str):
        config_paths = [config_paths]

    custom_component_roots.extend([str(p) for p in config_paths if str(p).strip()])

    env_paths = os.environ.get('WRITEHAT_COMPONENT_PATHS', '')
    if env_paths:
        custom_component_roots.extend([p for p in env_paths.split(os.pathsep) if p.strip()])

    resolved_paths = []
    observed_paths = set()
    project_root = Path(__file__).resolve().parent.parent.parent

    for p in custom_component_roots:
        path = Path(p).expanduser()
        if not path.is_absolute():
            path = project_root / path

        try:
            resolved = path.resolve()
        except FileNotFoundError:
            continue

        if not resolved.exists() or not resolved.is_dir():
            continue

        resolved_str = str(resolved)
        if resolved_str in observed_paths:
            continue

        observed_paths.add(resolved_str)
        resolved_paths.append(resolved)

    return resolved_paths


def _resolve_component_directory(root_path):
    root_path = Path(root_path)

    if (root_path / 'components').is_dir():
        return root_path, root_path / 'components'

    if root_path.name == 'components':
        return root_path.parent, root_path

    return root_path, root_path


def getCustomTemplateDirs():
    template_dirs = []
    for root_path in _get_custom_component_roots():
        plugin_root, _ = _resolve_component_directory(root_path)
        template_dir = plugin_root / 'templates'
        if template_dir.is_dir():
            template_dirs.append(str(template_dir))

    return template_dirs


def getCustomStaticDirs():
    static_dirs = []
    for root_path in _get_custom_component_roots():
        plugin_root, _ = _resolve_component_directory(root_path)
        static_dir = plugin_root / 'static'
        if static_dir.is_dir():
            static_dirs.append(str(static_dir))

    return static_dirs


def _get_component_source_paths():
    source_paths = []
    project_location = Path(__file__).resolve().parent.parent

    source_paths.append({
        'component_dir': project_location / 'components',
        'module_prefix': 'writehat.components',
        'source_name': 'core',
    })

    for idx, root_path in enumerate(_get_custom_component_roots()):
        _, component_dir = _resolve_component_directory(root_path)
        source_paths.append({
            'component_dir': component_dir,
            'module_prefix': f'writehat_custom_components_{idx}',
            'source_name': f'custom[{idx}]',
        })

    return source_paths


def _import_component(component_name, source):
    if source['module_prefix'] == 'writehat.components':
        return importlib.import_module(f"{source['module_prefix']}.{component_name}")

    component_file = Path(source['component_dir']) / f'{component_name}.py'
    module_name = f"{source['module_prefix']}.{component_name}"
    module_spec = importlib.util.spec_from_file_location(module_name, str(component_file))

    if module_spec is None or module_spec.loader is None:
        raise ImportError(f'Unable to load module spec for {component_file}')

    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_name] = module
    module_spec.loader.exec_module(module)
    return module



def createAdminUser():

    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", 'writehat.settings')
    import django
    django.setup()
    from django.contrib.auth.models import User
    from django.db import Error as DjangoError
    try:
        user = User.objects.create_superuser(
            username=writehat_config['writehat']['admin_username'],
            password=writehat_config['writehat']['admin_password']
        )
        user.save()
    except DjangoError:
        pass


def fixMigrationBug():

    filename = Path(__file__).parent.parent / 'migrations/__init__.py'
    try:
        filename.parent.mkdir(exist_ok=True)
        filename.touch()
    except:
        pass


# get a list of valid components
def getComponentList(componentType=None):

    detectedComponents = []
    masterComponentList = dict()
    source_paths = _get_component_source_paths()

    for source in source_paths:
        try:
            module_candidates = next(os.walk(source['component_dir']))[2]
        except StopIteration:
            continue

        for file in module_candidates:

            file = Path(file)

            if file.suffix == ('.py') and file.stem not in ['base'] \
                and (componentType is None or componentType == str(file.stem)):

                # make sure filename works as a python module
                if isValidStrictName(file.stem):
                    detectedComponents.append((file.stem, source))

    # for each detected file, try to import
    for detectedComponent, source in detectedComponents:

        if detectedComponent in masterComponentList:
            continue

        componentName = '{}.{}'.format(source['module_prefix'], detectedComponent)

        try:
            componentModule = _import_component(detectedComponent, source)

            componentClass = componentModule.Component
            componentClass.type = detectedComponent

            if componentType is not None and componentType == detectedComponent:
                # just return the class if it was requested
                return componentClass

            # otherwise, build a dictionary with all of them
            else:
                masterComponentList[detectedComponent] = componentClass

        except (ImportError, AttributeError) as e:
            print('[!] Error importing {}:\n{}\n'.format(componentName, str(e)))
            continue

    if componentType is not None:
        raise ComponentError('Component "{}" not found'.format(str(componentType)))

    return masterComponentList


# simpler JSON format
def getComponentListJSON():

    availableComponents = [{
        'name': c.default_name,
        'type': c.type,
        'isContainer': c.isContainer,
        'iconType': c.iconType,
        'iconColor': c.iconColor,
        'id': '',
    } for c in getComponentList().values()]
    availableComponents.sort(key=lambda x: x['name'])
    return availableComponents




def get_db_obj(host, port, database, username=None, password=None):
    '''
    Authenticates to mongodb and returns the databse object
    '''

    try:
        # Todo: encode UUIDs using newer v4 method in mongo?
        #codec_options = CodecOptions(document_class=RawBSONDocument)
        if password:
            client = pymongo.MongoClient(host, port, username=username, password=password)
        else:
            client = pymongo.MongoClient(host, port)
        db = client[database]

    except pymongo.errors.PyMongoError as e:
        error = str(e) + '\n'
        try:
            error += str(e.details)
        except AttributeError:
            pass
        raise DatabaseError(error)

    return db