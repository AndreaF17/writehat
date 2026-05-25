import logging
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from cvss import CVSS4 as CVSS4Calculator
from cvss import CVSS4Error, CVSSError


log = logging.getLogger(__name__)


class CVSS4:

    default_fields = OrderedDict([
        ('AV', OrderedDict([('N', None), ('A', None), ('L', None), ('P', None)])),
        ('AC', OrderedDict([('L', None), ('H', None)])),
        ('AT', OrderedDict([('N', None), ('P', None)])),
        ('PR', OrderedDict([('N', None), ('L', None), ('H', None)])),
        ('UI', OrderedDict([('N', None), ('P', None), ('A', None)])),
        ('VC', OrderedDict([('H', None), ('L', None), ('N', None)])),
        ('VI', OrderedDict([('H', None), ('L', None), ('N', None)])),
        ('VA', OrderedDict([('H', None), ('L', None), ('N', None)])),
        ('SC', OrderedDict([('H', None), ('L', None), ('N', None)])),
        ('SI', OrderedDict([('H', None), ('L', None), ('N', None)])),
        ('SA', OrderedDict([('H', None), ('L', None), ('N', None)])),
        ('E', OrderedDict([('X', None), ('A', None), ('P', None), ('U', None)])),
        ('CR', OrderedDict([('X', None), ('H', None), ('M', None), ('L', None)])),
        ('IR', OrderedDict([('X', None), ('H', None), ('M', None), ('L', None)])),
        ('AR', OrderedDict([('X', None), ('H', None), ('M', None), ('L', None)])),
        ('MAV', OrderedDict([('X', None), ('N', None), ('A', None), ('L', None), ('P', None)])),
        ('MAC', OrderedDict([('X', None), ('L', None), ('H', None)])),
        ('MAT', OrderedDict([('X', None), ('N', None), ('P', None)])),
        ('MPR', OrderedDict([('X', None), ('N', None), ('L', None), ('H', None)])),
        ('MUI', OrderedDict([('X', None), ('N', None), ('P', None), ('A', None)])),
        ('MVC', OrderedDict([('X', None), ('H', None), ('L', None), ('N', None)])),
        ('MVI', OrderedDict([('X', None), ('H', None), ('L', None), ('N', None)])),
        ('MVA', OrderedDict([('X', None), ('H', None), ('L', None), ('N', None)])),
        ('MSC', OrderedDict([('X', None), ('H', None), ('L', None), ('N', None)])),
        ('MSI', OrderedDict([('X', None), ('S', None), ('H', None), ('L', None), ('N', None)])),
        ('MSA', OrderedDict([('X', None), ('S', None), ('H', None), ('L', None), ('N', None)])),
    ])

    mandatory_fields = ['AV', 'AC', 'AT', 'PR', 'UI', 'VC', 'VI', 'VA', 'SC', 'SI', 'SA']

    @classmethod
    def fromDict(cls, d):

        return cls(cls.createVector(d))

    def __init__(self, vector):

        try:
            self._calculator = CVSS4Calculator(vector)
        except (CVSS4Error, CVSSError) as e:
            assert False, f'Invalid CVSS4 vector: {e}'

        self._vector = self.parseVector(self._calculator.clean_vector())

    @classmethod
    def createVector(cls, attributeList):

        valueList = OrderedDict()

        for field in cls.default_fields.keys():
            value = attributeList.get(field, attributeList.get(f'cvss4{field}', None))

            # cvss==3.6 does not accept SI:S or SA:S on base metrics. Convert stale
            # client values to the closest accepted severity value.
            if field in ('SI', 'SA') and value == 'S':
                value = 'H'

            if value in (None, ''):
                if field in cls.mandatory_fields:
                    value = cls.defaultChoice(field)
                else:
                    value = 'X'

            if value in cls.validChoices(field):
                valueList.update({field: value})
            else:
                assert False, f'Invalid CVSS4 value for {field}: {value}'

        vector_fields = []
        for field, value in valueList.items():
            if field in cls.mandatory_fields or value != 'X':
                vector_fields.append(f'{field}:{value}')

        vector = '/'.join(['CVSS:4.0'] + vector_fields)
        log.debug(f'Created CVSS4 vector: {vector}')

        return vector

    def parseVector(self, vector):

        try:
            fields = vector.split('/')[1:]
            vector_dict = {
                key: value
                for key, value in [field.split(':', 1) for field in fields if ':' in field]
            }
        except ValueError:
            assert False, f'Invalid CVSS4 vector: {vector}'

        vector_dict_validated = OrderedDict()

        for field in self.fieldNames:
            if field in vector_dict:
                vector_dict_validated.update({field: vector_dict[field]})
            elif field in self.mandatory_fields:
                assert False, f'Missing mandatory CVSS4 field {field}'
            else:
                vector_dict_validated.update({field: 'X'})

        return vector_dict_validated

    @property
    def vector(self):

        return self._calculator.clean_vector()

    @property
    def dict(self):

        return {f'cvss4{key}': value for key, value in self._vector.items()}

    @property
    def legacy_dict(self):

        d = self.dict
        return {
            'cvssAV': d['cvss4AV'],
            'cvssAC': d['cvss4AC'],
            'cvssPR': d['cvss4PR'],
            'cvssUI': d['cvss4UI'],
            'cvssS': d['cvss4SC'],
            'cvssC': d['cvss4VC'],
            'cvssI': d['cvss4VI'],
            'cvssA': d['cvss4VA'],
        }

    @property
    def fieldNames(self):

        return list(self.default_fields.keys())

    @classmethod
    def validChoices(cls, field):

        return list(cls.default_fields[field].keys())

    @classmethod
    def defaultChoice(cls, field):

        return next(iter(cls.default_fields[field].keys()))

    @property
    def score(self):

        return float(self._calculator.base_score)

    @property
    def severity(self):

        severity = self._calculator.severity
        if severity == 'None':
            return 'Informational'

        return severity

    def __str__(self):

        return self.vector
