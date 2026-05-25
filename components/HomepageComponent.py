from datetime import date, datetime
from .base import *

current_year = datetime.now().year
years = range(current_year - 5, current_year + 5)


class HomepageComponentForm(ComponentForm):
    class CustomDateWidget(forms.SelectDateWidget):
        template_name = "widgets/custom_date.html"

    componentText = forms.CharField(
        label='Component Text',
        widget=forms.Textarea,
        max_length=50000,
        required=False,
    )
    centerContent = forms.BooleanField(
        label='Center Content?',
        required=False,
        initial=False,
    )
    reportDate = forms.DateField(
        widget=CustomDateWidget(years=years),
        label='Report Date',
        required=False,
    )
    teamMember1Name = forms.CharField(label='Team Member 1 - Name', required=False)
    teamMember1Role = forms.CharField(label='Team Member 1 - Role', required=False)
    teamMember2Name = forms.CharField(label='Team Member 2 - Name', required=False)
    teamMember2Role = forms.CharField(label='Team Member 2 - Role', required=False)
    teamMember3Name = forms.CharField(label='Team Member 3 - Name', required=False)
    teamMember3Role = forms.CharField(label='Team Member 3 - Role', required=False)
    teamMember4Name = forms.CharField(label='Team Member 4 - Name', required=False)
    teamMember4Role = forms.CharField(label='Team Member 4 - Role', required=False)
    teamMember5Name = forms.CharField(label='Team Member 5 - Name', required=False)
    teamMember5Role = forms.CharField(label='Team Member 5 - Role', required=False)

    def clean_reportDate(self):
        report_date = self.cleaned_data.get('reportDate')
        if not report_date:
            return ''

        # JSON component docs are persisted in Mongo; store as string, not date object.
        return report_date.strftime('%Y-%m-%d')

    field_order = [
        'name',
        'componentText',
        'centerContent',
        'reportDate',
        'teamMember1Name',
        'teamMember1Role',
        'teamMember2Name',
        'teamMember2Role',
        'teamMember3Name',
        'teamMember3Role',
        'teamMember4Name',
        'teamMember4Role',
        'teamMember5Name',
        'teamMember5Role',
        'pageBreakBefore',
        'showTitle',
    ]


class Component(BaseComponent):
    default_name = 'Homepage Component'
    formClass = HomepageComponentForm
    fieldList = {
        'componentText': StringField(markdown=True, templatable=True),
        'centerContent': BoolField(templatable=True),
        'reportDate': StringField(templatable=True),
        'teamMember1Name': StringField(templatable=True),
        'teamMember1Role': StringField(templatable=True),
        'teamMember2Name': StringField(templatable=True),
        'teamMember2Role': StringField(templatable=True),
        'teamMember3Name': StringField(templatable=True),
        'teamMember3Role': StringField(templatable=True),
        'teamMember4Name': StringField(templatable=True),
        'teamMember4Role': StringField(templatable=True),
        'teamMember5Name': StringField(templatable=True),
        'teamMember5Role': StringField(templatable=True),
    }
    htmlTemplate = 'componentTemplates/HomepageComponent.html'
    includeInToc = False
    showTitle = False
    iconType = 'fas fa-house'
    iconColor = '#5bc0de'

    team_member_pairs = [
        ('teamMember1Name', 'teamMember1Role'),
        ('teamMember2Name', 'teamMember2Role'),
        ('teamMember3Name', 'teamMember3Role'),
        ('teamMember4Name', 'teamMember4Role'),
        ('teamMember5Name', 'teamMember5Role'),
    ]

    def preprocess(self, context):
        report_date = context.get('reportDate', '')
        if isinstance(report_date, datetime):
            context['formattedReportDate'] = report_date.strftime('%Y-%m-%d')
        elif isinstance(report_date, date):
            context['formattedReportDate'] = report_date.strftime('%Y-%m-%d')
        elif isinstance(report_date, str) and len(report_date.strip()):
            try:
                parsed = datetime.strptime(report_date.strip(), '%Y-%m-%d')
                context['formattedReportDate'] = parsed.strftime('%Y-%m-%d')
            except ValueError:
                context['formattedReportDate'] = report_date
        else:
            context['formattedReportDate'] = ''

        # Build centered title and subtitle content for the homepage block.
        configured_title = (context.get('name', '') or '').strip()
        if configured_title and configured_title != self.default_name:
            context['homepageTitle'] = configured_title
        else:
            report_name = getattr(context.get('report', None), 'name', '')
            context['homepageTitle'] = report_name or configured_title

        customer_name = ''
        engagement = context.get('engagement', None)
        if engagement is not None:
            customer = getattr(engagement, 'customer', None)
            if customer is not None:
                customer_name = (getattr(customer, 'name', '') or '').strip()
            if not customer_name:
                customer_name = (getattr(engagement, 'name', '') or '').strip()

        subtitle_parts = []
        if customer_name:
            subtitle_parts.append(customer_name)
        if context['formattedReportDate']:
            subtitle_parts.append(context['formattedReportDate'])
        context['homepageSubtitle'] = ' - '.join(subtitle_parts)

        team_rows = []
        for name_key, role_key in self.team_member_pairs:
            name_value = (context.get(name_key, '') or '').strip()
            role_value = (context.get(role_key, '') or '').strip()
            if name_value or role_value:
                team_rows.append({'name': name_value, 'role': role_value})

        context['teamRows'] = team_rows
        return context
