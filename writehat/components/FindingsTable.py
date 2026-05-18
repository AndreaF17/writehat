import logging
from .base import *

log = logging.getLogger(__name__)


class Component(BaseComponent):

    default_name = 'Summary of Findings'
    htmlTemplate = 'componentTemplates/FindingsTable.html'
    iconType = 'fas fa-th-list'
    iconColor = 'var(--orange)'

    def _get_finding_groups(self, report):
        if report is None:
            return []

        from writehat.lib.findingGroup import BaseFindingGroup

        try:
            finding_groups = BaseFindingGroup.filter_children(
                engagementParent=report.engagementParent
            )
        except Exception as e:
            log.warning(f'Failed to fetch finding groups for summary: {e}')
            return []

        finding_groups.sort(key=lambda fg: (getattr(fg, 'name', '') or '').lower())
        return finding_groups

    def preprocess(self, context):
        context = super().preprocess(context)

        report = context.get('report')
        summary_groups = []

        for finding_group in self._get_finding_groups(report):
            finding_group._report_object = report
            findings = list(finding_group.findings)
            if not findings:
                continue

            summary_groups.append({
                'group': finding_group,
                'findings': findings,
            })

        context['summary_groups'] = summary_groups
        return context