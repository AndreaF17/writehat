from django import forms
from writehat.lib.tooltipData import toolTipData 
from writehat.lib.widget import CategoryBootstrapSelect, CategoryBootstrapSelectEngagements, FindingGroupSelect, FindingBootstrapSelect, TooltipBase


class FindingForm(forms.Form):

    # override in child class
    scoringType = 'None'

    # Common fields across all findings
    name = forms.CharField(
        label='Finding Name', 
        widget=forms.TextInput(attrs={'class': 'name-validation'}),
        max_length=100)
    background = forms.CharField(
        label='Background',
        widget=forms.Textarea(),
        max_length=30000,
        required=False)
    remediation = forms.CharField(
        label='Remediation',
        widget=forms.Textarea(),
        max_length=30000,
        required=False)
    references = forms.CharField(
        label='References',
        widget=forms.Textarea(),
        max_length=30000,
        required=False)

    categoryID = forms.UUIDField(
        label='Category',
        widget=CategoryBootstrapSelectEngagements(
            attrs={'required': 'true'}
        ),
        required=True)

    @property
    def className(self):

        return type(self).__name__


class DREADForm(FindingForm):

    scoringType = 'DREAD'

    # make sure category goes first (after name)
    field_order = ['name', 'categoryID']
    choicesDread = (
        ('0', ('0')),
        ('1', ('1')),
        ('2', ('2')),
        ('3', ('3')),
        ('4', ('4')),
        ('5', ('5')),
        ('6', ('6')),
        ('7', ('7')),
        ('8', ('8')),
        ('9', ('9')),
        ('10', ('10')),
    )

    dreadDamage = forms.ChoiceField(choices=choicesDread,
        label='Damage',
        widget=TooltipBase(fieldName='damage', tooltipText=toolTipData['damage'], attrs={'class': 'custom-select'}),
        required=True)

    dreadReproducibility = forms.ChoiceField(choices=choicesDread,
        label='Reproducibility',
        widget=TooltipBase(fieldName='reproducibility', tooltipText=toolTipData['reproducibility'], attrs={'class': 'custom-select'}),
        required=True)

    dreadExploitability = forms.ChoiceField(choices=choicesDread,
        label='Exploitability',
        widget=TooltipBase(fieldName='exploitability', tooltipText=toolTipData['exploitability'], attrs={'class': 'custom-select'}),
        required=True)

    dreadAffectedUsers = forms.ChoiceField(choices=choicesDread,
        label='Affected Users',
        widget=TooltipBase(fieldName='affectedUsers', tooltipText=toolTipData['affectedUsers'], attrs={'class': 'custom-select'}),
        required=True)

    dreadDiscoverability = forms.ChoiceField(choices=choicesDread,
        label='Discoverability',
        widget=TooltipBase(fieldName='discoverability', tooltipText=toolTipData['discoverability'], attrs={'class': 'custom-select'}),
        required=True)                    



class ProactiveForm(FindingForm):

    scoringType = 'PROACTIVE'
    remediation = None
    # make sure category goes first (after name)
    field_order = ['name', 'categoryID']



class CVSSForm(FindingForm):

    scoringType = 'CVSS'

    # make sure category goes first (after name)
    toolsUsed = forms.CharField(
        label='Tools Used',
        widget=forms.Textarea(),
        max_length=30000,
        required=False)
    field_order = ['name','categoryID']
    proofOfConcept = forms.CharField(
        label='Proof of Concept',
        widget=forms.Textarea(attrs={'class': 'finding-database-exclude'}),
        max_length=30000,
        required=False)

    # CVSS Choices Definitions
    choicesAV = (
        ('N', ('Network')),
        ('A', ('Adjacent')),
        ('L', ('Local')),
        ('P', ('Physical'))
    )

    choicesMAV = (
        ('X', ('Not Defined')),
        ('N', ('Network')),
        ('A', ('Adjacent')),
        ('L', ('Local')),
        ('P', ('Physical'))
    )

    # Attack Complexity
    choicesAC = (
        ('L', ('Low')),
        ('H', ('High')),
    )

    choicesMAC = (
        ('X', ('Not Defined')),
        ('L', ('Low')),
        ('H', ('High')),
    )

    # Privileges Required
    choicesPR = (
        ('N', ('None')),
        ('L', ('Low')),
        ('H', ('High')),
    )

    # User Interaction
    choicesUI = (
        ('N', ('None')),
        ('R', ('Required')),
    )

    choicesMUI = (
        ('X', ('Not Defined')),
        ('N', ('None')),
        ('R', ('Required')),
    )

    # Scope
    choicesS = (
        ('U', ('Unchanged')),
        ('C', ('Changed')),
    )

    choicesMS = (
        ('X', ('Not Defined')),
        ('U', ('Unchanged')),
        ('C', ('Changed')),
    )

    # Generic None/Low/High
    choicesNLH = (
        ('N', ('None')),
        ('L', ('Low')),
        ('H', ('High')),
    )

    # Generic Enviromental Score NotDefined/Low/Medium/High
    choicesXLMH = (
       ('X', ('Not Defined')),
       ('L', ('Low')),
       ('M', ('Medium')),
       ('H', ('High')),
    )

    # Generic Enviromental Score NotDefined/Low/High
    choicesXLH = (
       ('X', ('Not Defined')),
       ('L', ('Low')),
       ('H', ('High')),
    )

    # TemporalScore Section
    choicesE = (
        ('X', ('Not Defined')),
        ('U', ('Unproven')),
        ('P', ('Proof-of-Concept')),
        ('F', ('Functional')),
        ('H', ('High')),
    )

    choicesRL = (
        ('X', ('Not Defined')),
        ('U', ('Unavailable')),
        ('W', ('Workaround')),
        ('T', ('Temporary Fix')),
        ('O', ('Official Fix')),
    )

    choicesRC = (
        ('X', ('Not Defined')),
        ('U', ('Unknown')),
        ('R', ('Reasonable')),
        ('C', ('Confirmed')),
    )


    ### CVSS FIELDS ###
    # Basic
    cvssAV = forms.ChoiceField(choices=choicesAV,
        label='Attack Vector',
        widget=TooltipBase(fieldName='AV', tooltipText=toolTipData['AV'], attrs={'class': 'custom-select'}),
        required=False)
    cvssAC = forms.ChoiceField(choices=choicesAC,
        label='Attack Complexity',
        widget=TooltipBase(fieldName='AC', tooltipText=toolTipData['AC'], attrs={'class': 'custom-select'}),
        required=False)
    cvssPR = forms.ChoiceField(choices=choicesPR,
        label='Privileges Required',
        widget=TooltipBase(fieldName='PR', tooltipText=toolTipData['PR'], attrs={'class': 'custom-select'}),
        required=False)
    cvssUI = forms.ChoiceField(choices=choicesUI,
        label='User Interaction',
        widget=TooltipBase(fieldName='UI', tooltipText=toolTipData['UI'], attrs={'class': 'custom-select'}),
        required=False)
    cvssS = forms.ChoiceField(choices=choicesS,
        label='Scope',
        widget=TooltipBase(fieldName='S', tooltipText=toolTipData['S'], attrs={'class': 'custom-select'}),
        required=False)
    cvssC = forms.ChoiceField(choices=choicesNLH,
        label='Confidentiality',
        widget=TooltipBase(fieldName='C', tooltipText=toolTipData['C'], attrs={'class': 'custom-select'}),
        required=False)
    cvssI = forms.ChoiceField(choices=choicesNLH,
        label='Integrity',
        widget=TooltipBase(fieldName='I', tooltipText=toolTipData['I'], attrs={'class': 'custom-select'}),
        required=False)
    cvssA = forms.ChoiceField(choices=choicesNLH,
        label='Availability',
        widget=TooltipBase(fieldName='A', tooltipText=toolTipData['A'], attrs={'class': 'custom-select'}),
        required=False)

    # Advanced
    cvssE = forms.ChoiceField(choices=choicesE,
        label='Exploit Code Maturity',
        widget=TooltipBase(fieldName='E', tooltipText=toolTipData['E'], attrs={'class': 'custom-select finding-advanced-choice'}),
        required=True, initial='X')
    cvssRL = forms.ChoiceField(choices=choicesRL,
        label='Remediation Level',
        widget=TooltipBase(fieldName='RL', tooltipText=toolTipData['RL'], attrs={'class': 'custom-select finding-advanced-choice'}),
        required=True, initial='X')
    cvssRC = forms.ChoiceField(choices=choicesRC,
        label='Report Confidence',
        widget=TooltipBase(fieldName='RC', tooltipText=toolTipData['RC'], attrs={'class': 'custom-select finding-advanced-choice'}),
        required=True, initial='X')
    cvssCR = forms.ChoiceField(choices=choicesXLMH,
        label='Confidentiality Requirement',
        widget=TooltipBase(fieldName='CR', tooltipText=toolTipData['CR'], attrs={'class': 'custom-select finding-advanced-choice'}),
        required=True, initial='X')
    cvssIR = forms.ChoiceField(choices=choicesXLMH,
        label='Integrity Requirement',
        widget=TooltipBase(fieldName='IR', tooltipText=toolTipData['IR'], attrs={'class': 'custom-select finding-advanced-choice'}),
        required=True, initial='X')
    cvssAR = forms.ChoiceField(choices=choicesXLMH,
        label='Availability Requirement',
        widget=TooltipBase(fieldName='AR', tooltipText=toolTipData['AR'], attrs={'class': 'custom-select finding-advanced-choice'}),
        required=True, initial='X')
    cvssMAV= forms.ChoiceField(choices=choicesMAV,
        label='Modified Attack Vector',
        widget=TooltipBase(fieldName='MAV', tooltipText=toolTipData['MAV'], attrs={'class': 'custom-select finding-advanced-choice'}),
        required=True, initial='X')
    cvssMAC = forms.ChoiceField(choices=choicesMAC,
        label='Modified Attack Complexity',
        widget=TooltipBase(fieldName='MAC', tooltipText=toolTipData['MAC'], attrs={'class': 'custom-select finding-advanced-choice'}),
        required=True, initial='X')
    cvssMPR = forms.ChoiceField(choices=choicesXLH,
        label='Modified Privileges Required',
        widget=TooltipBase(fieldName='MPR', tooltipText=toolTipData['MPR'], attrs={'class': 'custom-select finding-advanced-choice'}),
        required=True, initial='X')
    cvssMUI = forms.ChoiceField(choices=choicesMUI,
        label='Modified User Interaction',
        widget=TooltipBase(fieldName='MUI', tooltipText=toolTipData['MUI'], attrs={'class': 'custom-select finding-advanced-choice'}),
        required=True, initial='X')
    cvssMS = forms.ChoiceField(choices=choicesMS,
        label='Modified Scope',
        widget=TooltipBase(fieldName='MS', tooltipText=toolTipData['MS'], attrs={'class': 'custom-select finding-advanced-choice'}),
        required=True, initial='X')
    cvssMC = forms.ChoiceField(choices=choicesXLH,
        label='Modified Confidentiality',
        widget=TooltipBase(fieldName='MC', tooltipText=toolTipData['MC'], attrs={'class': 'custom-select finding-advanced-choice'}),
        required=True, initial='X')
    cvssMI = forms.ChoiceField(choices=choicesXLH,
        label='Modified Integrity',
        widget=TooltipBase(fieldName='MI', tooltipText=toolTipData['MI'], attrs={'class': 'custom-select finding-advanced-choice'}),
        required=True, initial='X')
    cvssMA = forms.ChoiceField(choices=choicesXLH,
        label='Modified Availability',
        widget=TooltipBase(fieldName='MA', tooltipText=toolTipData['MA'], attrs={'class': 'custom-select finding-advanced-choice'}),
        required=True, initial='X')


class CVSS4Form(FindingForm):

    scoringType = 'CVSS4'

    toolsUsed = forms.CharField(
        label='Tools Used',
        widget=forms.Textarea(),
        max_length=30000,
        required=False)
    field_order = ['name', 'categoryID']
    proofOfConcept = forms.CharField(
        label='Proof of Concept',
        widget=forms.Textarea(attrs={'class': 'finding-database-exclude'}),
        max_length=30000,
        required=False)

    choicesAV = (
        ('N', ('Network')),
        ('A', ('Adjacent')),
        ('L', ('Local')),
        ('P', ('Physical')),
    )

    choicesAC = (
        ('L', ('Low')),
        ('H', ('High')),
    )

    choicesAT = (
        ('N', ('None')),
        ('P', ('Present')),
    )

    choicesPR = (
        ('N', ('None')),
        ('L', ('Low')),
        ('H', ('High')),
    )

    choicesUI = (
        ('N', ('None')),
        ('P', ('Passive')),
        ('A', ('Active')),
    )

    choicesHLN = (
        ('H', ('High')),
        ('L', ('Low')),
        ('N', ('None')),
    )

    choicesSHLN = (
        ('S', ('Safety')),
        ('H', ('High')),
        ('L', ('Low')),
        ('N', ('None')),
    )

    choicesE = (
        ('X', ('Not Defined')),
        ('A', ('Attacked')),
        ('P', ('Proof-of-Concept')),
        ('U', ('Unreported')),
    )

    choicesXHML = (
        ('X', ('Not Defined')),
        ('H', ('High')),
        ('M', ('Medium')),
        ('L', ('Low')),
    )

    choicesXMAV = (
        ('X', ('Not Defined')),
        ('N', ('Network')),
        ('A', ('Adjacent')),
        ('L', ('Local')),
        ('P', ('Physical')),
    )

    choicesXAC = (
        ('X', ('Not Defined')),
        ('L', ('Low')),
        ('H', ('High')),
    )

    choicesXAT = (
        ('X', ('Not Defined')),
        ('N', ('None')),
        ('P', ('Present')),
    )

    choicesXPR = (
        ('X', ('Not Defined')),
        ('N', ('None')),
        ('L', ('Low')),
        ('H', ('High')),
    )

    choicesXUI = (
        ('X', ('Not Defined')),
        ('N', ('None')),
        ('P', ('Passive')),
        ('A', ('Active')),
    )

    choicesXHLN = (
        ('X', ('Not Defined')),
        ('H', ('High')),
        ('L', ('Low')),
        ('N', ('None')),
    )

    choicesXSHLN = (
        ('X', ('Not Defined')),
        ('S', ('Safety')),
        ('H', ('High')),
        ('L', ('Low')),
        ('N', ('None')),
    )

    cvss4AV = forms.ChoiceField(choices=choicesAV,
        label='Attack Vector',
        widget=TooltipBase(fieldName='AV', tooltipText=toolTipData['AV'], attrs={'class': 'custom-select'}),
        required=False)
    cvss4AC = forms.ChoiceField(choices=choicesAC,
        label='Attack Complexity',
        widget=TooltipBase(fieldName='AC', tooltipText=toolTipData['AC'], attrs={'class': 'custom-select'}),
        required=False)
    cvss4AT = forms.ChoiceField(choices=choicesAT,
        label='Attack Requirements',
        widget=TooltipBase(fieldName='AT', tooltipText=toolTipData['AT'], attrs={'class': 'custom-select'}),
        required=False)
    cvss4PR = forms.ChoiceField(choices=choicesPR,
        label='Privileges Required',
        widget=TooltipBase(fieldName='PR', tooltipText=toolTipData['PR'], attrs={'class': 'custom-select'}),
        required=False)
    cvss4UI = forms.ChoiceField(choices=choicesUI,
        label='User Interaction',
        widget=TooltipBase(fieldName='UI', tooltipText=toolTipData['UI'], attrs={'class': 'custom-select'}),
        required=False)
    cvss4VC = forms.ChoiceField(choices=choicesHLN,
        label='Vulnerable Confidentiality',
        widget=TooltipBase(fieldName='VC', tooltipText=toolTipData['VC'], attrs={'class': 'custom-select'}),
        required=False)
    cvss4VI = forms.ChoiceField(choices=choicesHLN,
        label='Vulnerable Integrity',
        widget=TooltipBase(fieldName='VI', tooltipText=toolTipData['VI'], attrs={'class': 'custom-select'}),
        required=False)
    cvss4VA = forms.ChoiceField(choices=choicesHLN,
        label='Vulnerable Availability',
        widget=TooltipBase(fieldName='VA', tooltipText=toolTipData['VA'], attrs={'class': 'custom-select'}),
        required=False)
    cvss4SC = forms.ChoiceField(choices=choicesHLN,
        label='Subsequent Confidentiality',
        widget=TooltipBase(fieldName='SC', tooltipText=toolTipData['SC'], attrs={'class': 'custom-select'}),
        required=False)
    cvss4SI = forms.ChoiceField(choices=choicesHLN,
        label='Subsequent Integrity',
        widget=TooltipBase(fieldName='SI', tooltipText=toolTipData['SI'], attrs={'class': 'custom-select'}),
        required=False)
    cvss4SA = forms.ChoiceField(choices=choicesHLN,
        label='Subsequent Availability',
        widget=TooltipBase(fieldName='SA', tooltipText=toolTipData['SA'], attrs={'class': 'custom-select'}),
        required=False)

    cvss4E = forms.ChoiceField(choices=choicesE,
        label='Exploit Maturity',
        widget=TooltipBase(fieldName='E', tooltipText=toolTipData['E'], attrs={'class': 'custom-select finding-advanced-choice'}),
        required=True, initial='X')
    cvss4CR = forms.ChoiceField(choices=choicesXHML,
        label='Confidentiality Requirement',
        widget=TooltipBase(fieldName='CR', tooltipText=toolTipData['CR'], attrs={'class': 'custom-select finding-advanced-choice'}),
        required=True, initial='X')
    cvss4IR = forms.ChoiceField(choices=choicesXHML,
        label='Integrity Requirement',
        widget=TooltipBase(fieldName='IR', tooltipText=toolTipData['IR'], attrs={'class': 'custom-select finding-advanced-choice'}),
        required=True, initial='X')
    cvss4AR = forms.ChoiceField(choices=choicesXHML,
        label='Availability Requirement',
        widget=TooltipBase(fieldName='AR', tooltipText=toolTipData['AR'], attrs={'class': 'custom-select finding-advanced-choice'}),
        required=True, initial='X')
    cvss4MAV = forms.ChoiceField(choices=choicesXMAV,
        label='Modified Attack Vector',
        widget=TooltipBase(fieldName='MAV', tooltipText=toolTipData['MAV'], attrs={'class': 'custom-select finding-advanced-choice'}),
        required=True, initial='X')
    cvss4MAC = forms.ChoiceField(choices=choicesXAC,
        label='Modified Attack Complexity',
        widget=TooltipBase(fieldName='MAC', tooltipText=toolTipData['MAC'], attrs={'class': 'custom-select finding-advanced-choice'}),
        required=True, initial='X')
    cvss4MAT = forms.ChoiceField(choices=choicesXAT,
        label='Modified Attack Requirements',
        widget=TooltipBase(fieldName='MAT', tooltipText=toolTipData['MAT'], attrs={'class': 'custom-select finding-advanced-choice'}),
        required=True, initial='X')
    cvss4MPR = forms.ChoiceField(choices=choicesXPR,
        label='Modified Privileges Required',
        widget=TooltipBase(fieldName='MPR', tooltipText=toolTipData['MPR'], attrs={'class': 'custom-select finding-advanced-choice'}),
        required=True, initial='X')
    cvss4MUI = forms.ChoiceField(choices=choicesXUI,
        label='Modified User Interaction',
        widget=TooltipBase(fieldName='MUI', tooltipText=toolTipData['MUI'], attrs={'class': 'custom-select finding-advanced-choice'}),
        required=True, initial='X')
    cvss4MVC = forms.ChoiceField(choices=choicesXHLN,
        label='Modified Vulnerable Confidentiality',
        widget=TooltipBase(fieldName='MVC', tooltipText=toolTipData['MVC'], attrs={'class': 'custom-select finding-advanced-choice'}),
        required=True, initial='X')
    cvss4MVI = forms.ChoiceField(choices=choicesXHLN,
        label='Modified Vulnerable Integrity',
        widget=TooltipBase(fieldName='MVI', tooltipText=toolTipData['MVI'], attrs={'class': 'custom-select finding-advanced-choice'}),
        required=True, initial='X')
    cvss4MVA = forms.ChoiceField(choices=choicesXHLN,
        label='Modified Vulnerable Availability',
        widget=TooltipBase(fieldName='MVA', tooltipText=toolTipData['MVA'], attrs={'class': 'custom-select finding-advanced-choice'}),
        required=True, initial='X')
    cvss4MSC = forms.ChoiceField(choices=choicesXHLN,
        label='Modified Subsequent Confidentiality',
        widget=TooltipBase(fieldName='MSC', tooltipText=toolTipData['MSC'], attrs={'class': 'custom-select finding-advanced-choice'}),
        required=True, initial='X')
    cvss4MSI = forms.ChoiceField(choices=choicesXSHLN,
        label='Modified Subsequent Integrity',
        widget=TooltipBase(fieldName='MSI', tooltipText=toolTipData['MSI'], attrs={'class': 'custom-select finding-advanced-choice'}),
        required=True, initial='X')
    cvss4MSA = forms.ChoiceField(choices=choicesXSHLN,
        label='Modified Subsequent Availability',
        widget=TooltipBase(fieldName='MSA', tooltipText=toolTipData['MSA'], attrs={'class': 'custom-select finding-advanced-choice'}),
        required=True, initial='X')



class CategoryAddForm(forms.Form):

    categoryAddName = forms.CharField(
        label='Category Name',
        widget=forms.TextInput(attrs={'class': 'name-validation', 'required': 'true'}),
        max_length=1000)
    categoryAddID = forms.UUIDField(
        label='Parent Category',
        widget=CategoryBootstrapSelect)



class FindingImportForm(forms.Form):

    def __init__(self, *args, **kwargs):
        scoringType = kwargs.pop('scoringType') 
        super(FindingImportForm, self).__init__(*args, **kwargs)
        self.fields['finding'].widget = FindingBootstrapSelect(scoringType=scoringType)

    finding = forms.UUIDField(label='Finding')



### FINDING GROUPS ###

# Finding Group Types
choicesFgroup = (
    ('CVSS', ('CVSS 3.1')),
    ('CVSS4', ('CVSS 4.0')),
    ('DREAD', ('DREAD Framework')),
    ('PROACTIVE', ('Proactive / Positive')),
)


class FgroupForm(forms.Form):
    name = forms.CharField(
        label='Finding Group Name', 
        widget=forms.TextInput(
            attrs={
                'class': 'name-validation',
                'required': 'true'
            }
        ),
        max_length=100)
    prefix = forms.CharField(
        label='Finding Prefix',
        widget=forms.TextInput(
            attrs={'class': 'name-validation'}
        ),
        max_length=50)


class NewFgroupForm(FgroupForm):

    scoringType = forms.ChoiceField(
        choices=choicesFgroup,
        label='Findings Group Type',
        required=True)


class EditFgroupForm(FgroupForm):
    pass



### ENGAGEMENTS ###

class EngagementFindingForm(forms.Form):

    description = forms.CharField(
        label='Description',
        widget=forms.Textarea(attrs={'class': 'finding-database-exclude'}),
        max_length=30000,
        required=False)
    affectedResources = forms.CharField(
        label='Affected Resources',
        widget=forms.Textarea(attrs={'class': 'finding-database-exclude'}),
        max_length=30000,
        required=False)

    def __init__(self, *args, **kwargs):

        try:
            engagementParent = kwargs.pop('engagementParent')
            scoringType = kwargs.pop('scoringType')
        except KeyError:
            engagementParent = None
            scoringType = None

        super().__init__(*args, **kwargs)

        if engagementParent and scoringType:
            self.fields['findingGroup'].widget = FindingGroupSelect(
                attrs={'required': 'true'},
                engagementId=engagementParent,
                scoringType=scoringType
            )





class CVSSEngagementFindingForm(EngagementFindingForm,CVSSForm):

    findingGroup = forms.UUIDField(label='Finding Group',required=True)
    field_order = ['name','findingGroup','categoryID','description','affectedResources','background','proofOfConcept','toolsUsed','remediation','references','cvssAV','cvssAC','cvssPR','cvssUI','cvssS','cvssC','cvssI','cvssA','cvssE','cvssRL','cvssRC','cvssCR','cvssIR','cvssAR','cvssMAV','cvssMAC','cvssMPR','cvssMUI','cvssMS','cvssMC','cvssMI','cvssMA',]


class CVSS4EngagementFindingForm(EngagementFindingForm, CVSS4Form):

    findingGroup = forms.UUIDField(label='Finding Group', required=True)
    field_order = [
        'name',
        'findingGroup',
        'categoryID',
        'description',
        'affectedResources',
        'background',
        'proofOfConcept',
        'toolsUsed',
        'remediation',
        'references',
        'cvss4AV',
        'cvss4AC',
        'cvss4AT',
        'cvss4PR',
        'cvss4UI',
        'cvss4VC',
        'cvss4VI',
        'cvss4VA',
        'cvss4SC',
        'cvss4SI',
        'cvss4SA',
        'cvss4E',
        'cvss4CR',
        'cvss4IR',
        'cvss4AR',
        'cvss4MAV',
        'cvss4MAC',
        'cvss4MAT',
        'cvss4MPR',
        'cvss4MUI',
        'cvss4MVC',
        'cvss4MVI',
        'cvss4MVA',
        'cvss4MSC',
        'cvss4MSI',
        'cvss4MSA',
    ]


class DREADEngagementFindingForm(EngagementFindingForm,DREADForm):

    choicesStride = [ 
        ("spoofing",    "Spoofing"),
        ("tampering",   "Tampering"),
        ("repudiation", "Repudiation"),
        ("disclosure",  "Information Disclosure"),
        ("denial",      "Denial of Service"),
        ("privesc",     "Elevation of Privilege")
    ]

    findingGroup = forms.UUIDField(label='Finding Group',required=True)

    dreadImpact = forms.MultipleChoiceField( choices=choicesStride,
        label='Impact', required=False, widget=forms.SelectMultiple(
            attrs={'class': 'custom-select form-control selectpicker', 'multiple': 'multiple'}))
    descDamage = forms.CharField( label='Damage Detail',
        widget=forms.Textarea(), max_length=30000, required=False)
    descReproducibility = forms.CharField( label='Reproducibility Detail',
        widget=forms.Textarea(), max_length=30000, required=False)
    descExploitability = forms.CharField( label='Exploitability Detail',
        widget=forms.Textarea(), max_length=30000, required=False)
    descAffectedUsers = forms.CharField( label='Affected Users Detail',
        widget=forms.Textarea(), max_length=30000, required=False)
    descDiscoverability = forms.CharField( label='Discoverability Detail',
        widget=forms.Textarea(), max_length=30000, required=False)

    field_order = [
        'name',
        'findingGroup',
        'categoryID',
        'description',
        'affectedResources',
        'dreadImpact',
        'background',
        'remediation',
        'references',
        'dreadDamage',
        'descDamage',
        'dreadReproducibility',
        'descReproducibility',
        'dreadExploitability',
        'descExploitability',
        'dreadAffectedUsers',
        'descAffectedUsers',
        'dreadDiscoverability',
        'descDiscoverability'
    ]


class ProactiveEngagementFindingForm(EngagementFindingForm,ProactiveForm):

    findingGroup = forms.UUIDField(label='Finding Group',required=True)
    field_order = ['name','findingGroup','categoryID','description','affectedResources','background','references']


class CVSSDatabaseFindingForm(CVSSForm):
    findingGroup = None


class CVSS4DatabaseFindingForm(CVSS4Form):
    findingGroup = None

class DREADDatabaseFindingForm(DREADForm):
    findingGroup = None

class ProactiveDatabaseFindingForm(ProactiveForm):
    findingGroup = None
