import logging

from .base import *

log = logging.getLogger(__name__)


class Component(BaseComponent):

    default_name = 'Findings (Abridged + Full)'
    htmlTemplate = 'componentTemplates/FindingsCombined.html'
    iconType = 'fas fa-layer-group'
    iconColor = 'var(--cvss-color)'

    def _get_finding_groups(self, report):
        if report is None:
            return []

        from writehat.lib.findingGroup import BaseFindingGroup

        try:
            finding_groups = BaseFindingGroup.filter_children(
                engagementParent=report.engagementParent
            )
        except Exception as e:
            log.warning(f'Failed to fetch finding groups: {e}')
            return []

        finding_groups.sort(key=lambda fg: (getattr(fg, 'name', '') or '').lower())
        return finding_groups

    def preprocess(self, context):
        context = super().preprocess(context)

        report = context.get('report')
        index_prefix = self._resolve_index_prefix(report)
        group_sections = []
        group_counter = 0
        for finding_group in self._get_finding_groups(report):
            finding_group._report_object = report
            findings = list(finding_group.findings)
            if not findings:
                continue

            group_counter += 1
            if index_prefix:
                group_index = f'{index_prefix}.{group_counter}.'
            else:
                group_index = f'{group_counter}.'

            group_sections.append({
                'group': finding_group,
                'findings': findings,
                'toc_index': group_index,
            })

        context['group_sections'] = group_sections
        return context

    def _resolve_index_prefix(self, report):
        direct_index = (getattr(self, 'index', '') or '').strip('.')
        if direct_index:
            return direct_index

        if report is None:
            return ''

        target_id = str(self.id)

        def walk(components, prefix=''):
            counter = 0
            for component in components:
                component_prefix = prefix
                if component.includeInToc and component.showTitle:
                    counter += 1
                    component_prefix = f'{prefix}{counter}.'

                if str(component.id) == target_id:
                    return component_prefix.strip('.')

                children = getattr(component, 'children', []) or []
                if children:
                    resolved = walk(children, component_prefix)
                    if resolved is not None:
                        return resolved

            return None

        resolved_index = walk(report.components)
        return resolved_index or ''

    def toc_entries(self):
        entries = []

        if not self.includeInToc:
            return entries

        report = self.report
        index_prefix = self._resolve_index_prefix(report)
        counter = 0

        for finding_group in self._get_finding_groups(report):
            finding_group._report_object = report
            findings = list(finding_group.findings)
            if not findings:
                continue

            counter += 1
            if index_prefix:
                group_index = f'{index_prefix}.{counter}.'
            else:
                group_index = f'{counter}.'

            entries.append({
                'name': finding_group.name,
                'id': f'{self.id}_group_{counter}',
                'level': self.level,
                'index': group_index,
            })

        return entries