import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_dimensions.dart';
import '../../core/theme/app_typography.dart';
import '../../core/utils/context_ext.dart';
import '../../core/utils/enum_present.dart';
import '../../core/utils/formatters.dart';
import '../../features/history/history_controller.dart';
import '../../models/analysis_result.dart';
import '../../models/history_item.dart';
import '../../navigation/app_routes.dart';
import '../../repositories/report_repository.dart';
import '../../services/share_service.dart';
import '../../widgets/app_button.dart';
import '../../widgets/app_card.dart';
import '../../widgets/indicator_card.dart';
import '../../widgets/key_value_row.dart';
import '../../widgets/score_bar.dart';
import '../../widgets/section_header.dart';
import '../../widgets/verdict_badge.dart';

class ReportDetailsScreen extends StatefulWidget {
  final ReportArgs args;

  const ReportDetailsScreen({super.key, required this.args});

  @override
  State<ReportDetailsScreen> createState() => _ReportDetailsScreenState();
}

class _ReportDetailsScreenState extends State<ReportDetailsScreen> {
  late final AnalysisResult result = widget.args.result;
  bool _saved = false;
  String? _busy;

  Future<void> _save() async {
    if (_saved) return;
    await context.read<HistoryController>().add(
          HistoryItem(
            id: result.id,
            fileName: result.fileName,
            verdict: result.verdict,
            confidence: result.confidence,
            riskLevel: result.riskLevel,
            timestamp: result.timestamp,
          ),
        );
    if (!mounted) return;
    setState(() => _saved = true);
    context.showSnack('Saved to history');
  }

  Future<void> _exportPdf() async {
    setState(() => _busy = 'export');
    try {
      final repo = context.read<ReportRepository>();
      final share = context.read<ShareService>();
      final bytes = await repo.generatePdf(result);
      await share.sharePdf(bytes, 'chai-report.pdf');
    } catch (_) {
      if (mounted) context.showSnack('Could not generate the report.');
    } finally {
      if (mounted) setState(() => _busy = null);
    }
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    final verdictColor = result.verdict.color(colors);
    final prov = result.provenance;
    final isSightengineOk = prov?.isSightengineAvailable ?? false;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Report Details'),
        actions: [
          IconButton(
            tooltip: 'Export PDF',
            icon: const Icon(Icons.picture_as_pdf_outlined),
            onPressed: _busy == null ? _exportPdf : null,
          ),
        ],
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(AppSpacing.lg),
          children: [
            // =========================================================
            // 1. PRIMARY: AUTHENTICITY DETECTION
            // =========================================================
            AppCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Chai AI',
                            style: AppTypography.caption(colors.textTertiary),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'Authenticity Detection',
                            style: AppTypography.title(colors.textPrimary),
                          ),
                        ],
                      ),
                      VerdictBadge(
                          verdict: result.verdict,
                          confidence: result.confidence),
                    ],
                  ),
                  const SizedBox(height: AppSpacing.md),
                  Divider(color: colors.border),
                  const SizedBox(height: AppSpacing.sm),
                  KeyValueRow(
                      label: 'Analyzed File',
                      value: result.fileName ?? 'Image'),
                  KeyValueRow(
                    label: 'Timestamp',
                    value: AppFormatters.dateTime(result.timestamp),
                    divider: true,
                  ),
                  KeyValueRow(
                    label: 'Analysis Duration',
                    value: AppFormatters.duration(result.analysisDuration),
                    divider: true,
                  ),
                  KeyValueRow(
                    label: 'Risk Level',
                    value: result.riskLevel.label,
                    divider: true,
                  ),
                  KeyValueRow(
                    label: 'Confidence',
                    value: AppFormatters.percent(result.confidence),
                  ),
                  const SizedBox(height: AppSpacing.md),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(AppSpacing.md),
                    decoration: BoxDecoration(
                      color: verdictColor.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(AppRadius.md),
                      border:
                          Border.all(color: verdictColor.withValues(alpha: 0.3)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Decision Summary',
                          style: AppTypography.caption(verdictColor)
                              .copyWith(fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 4),
                        Text(
                          result.explanation,
                          style: AppTypography.body(colors.textPrimary),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: AppSpacing.md),
                  // Source attribution summary
                  Row(
                    children: [
                      Icon(
                        isSightengineOk
                            ? Icons.verified_user_outlined
                            : Icons.info_outline,
                        size: 16,
                        color:
                            isSightengineOk ? colors.success : colors.warning,
                      ),
                      const SizedBox(width: AppSpacing.xs),
                      Expanded(
                        child: Text(
                          isSightengineOk
                              ? 'Primary: Sightengine | Assisted by: Chai AI Forensics'
                              : 'External verification unavailable; classified by Chai forensics only.',
                          style: AppTypography.caption(
                            isSightengineOk ? colors.success : colors.warning,
                          ),
                        ),
                      ),

                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.xl),

            // =========================================================
            // 2. SECONDARY: IMAGE INSIGHTS
            // =========================================================
            SectionHeader(
              title: 'Image Insights',
              subtitle: 'Information extracted by Chai forensic pipeline',
            ),
            const SizedBox(height: AppSpacing.md),

            // Visual & Signal Analysis
            AppCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Visual & Signal Analysis',
                    style: AppTypography.label(colors.textPrimary),
                  ),
                  const SizedBox(height: AppSpacing.sm),
                  for (final score in result.scores)
                    ScoreBar(category: score.category, value: score.value),
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.lg),

            // Detected Indicators
            if (result.indicators.isNotEmpty) ...[
              SectionHeader(
                title: 'Forensic Indicators',
                subtitle: '${result.indicators.length} signals detected',
              ),
              const SizedBox(height: AppSpacing.md),
              for (final indicator in result.indicators)
                Padding(
                  padding: const EdgeInsets.only(bottom: AppSpacing.sm),
                  child: IndicatorCard(indicator: indicator),
                ),
              const SizedBox(height: AppSpacing.lg),
            ],

            // Forensic Evidence
            if (result.evidence.isNotEmpty) ...[
              SectionHeader(title: 'Forensic Evidence'),
              const SizedBox(height: AppSpacing.md),
              AppCard(
                child: Column(
                  children: [
                    for (final evidence in result.evidence)
                      Padding(
                        padding:
                            const EdgeInsets.symmetric(vertical: AppSpacing.sm),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Icon(Icons.chevron_right,
                                size: 16, color: colors.textTertiary),
                            const SizedBox(width: AppSpacing.sm),
                            Expanded(
                              child: Text(
                                evidence,
                                style: AppTypography.body(colors.textSecondary),
                              ),
                            ),
                          ],
                        ),
                      ),
                  ],
                ),
              ),
              const SizedBox(height: AppSpacing.lg),
            ],

            // Image Metadata
            if (result.metadata.isNotEmpty) ...[
              SectionHeader(title: 'Image Information & Metadata'),
              const SizedBox(height: AppSpacing.md),
              AppCard(
                child: Column(
                  children: [
                    for (final entry in result.metadata.entries)
                      if (!entry.key.startsWith('prov:'))
                        KeyValueRow(label: entry.key, value: entry.value),
                  ],
                ),
              ),
              const SizedBox(height: AppSpacing.lg),
            ],

            // Forensic Heatmap Preview
            if (result.heatmap != null) ...[
              SectionHeader(
                title: 'Forensic Visualizations',
                subtitle: 'Regions highlighted by Chai image analysis',
              ),
              const SizedBox(height: AppSpacing.md),
              AppCard(
                padding: EdgeInsets.zero,
                onTap: () => Navigator.of(context).pushNamed(
                  AppRoutes.heatmap,
                  arguments: HeatmapArgs(result),
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(AppRadius.lg),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Padding(
                        padding: const EdgeInsets.all(AppSpacing.md),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              'Visual Highlights',
                              style: AppTypography.label(colors.textPrimary),
                            ),
                            Text(
                              'View Full Heatmap →',
                              style: AppTypography.caption(colors.accent),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: AppSpacing.lg),
            ],

            // Detection Provenance Summary
            if (prov != null) ...[
              SectionHeader(title: 'Detection Provenance'),
              const SizedBox(height: AppSpacing.md),
              AppCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    KeyValueRow(
                      label: 'Final Classification',
                      value: prov.finalClassification.label,
                    ),
                    KeyValueRow(
                      label: 'Final Confidence',
                      value: '${(prov.finalConfidence * 100).round()}%',
                      divider: true,
                    ),
                    KeyValueRow(
                      label: 'Fused AI Probability',
                      value:
                          '${(prov.finalFusedProbability * 100).toStringAsFixed(1)}%',
                      divider: true,
                    ),
                    KeyValueRow(
                      label: 'Sightengine Status',
                      value: prov.sightengineStatus,
                      divider: true,
                    ),
                    if (prov.sightengineAiProbability != null)
                      KeyValueRow(
                        label: 'Sightengine AI Prob',
                        value:
                            '${(prov.sightengineAiProbability! * 100).toStringAsFixed(1)}%',
                        divider: true,
                      ),
                    KeyValueRow(
                      label: 'Sightengine Weight',
                      value: '${(prov.fusionWeightSightengine * 100).round()}%',
                      divider: true,
                    ),
                    KeyValueRow(
                      label: 'Chai Forensic Role',
                      value: 'Assisting Sightengine Verification',
                      divider: true,
                    ),
                    KeyValueRow(
                      label: 'Chai Forensic Telemetry',
                      value: 'Active (7 signals)',
                      divider: true,
                    ),
                    KeyValueRow(
                      label: 'Chai Edit / Artifact Score',
                      value:
                          '${(prov.chaiEditScore * 100).toStringAsFixed(1)}%',
                      divider: true,
                    ),

                    if (prov.decisionReason.isNotEmpty) ...[
                      const SizedBox(height: AppSpacing.sm),
                      Text(
                        'Decision Rationale:',
                        style: AppTypography.caption(colors.textTertiary),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        prov.decisionReason,
                        style: AppTypography.body(colors.textSecondary),
                      ),
                    ],
                  ],
                ),
              ),
              const SizedBox(height: AppSpacing.xl),
            ],


            // Action Buttons
            AppButton(
              label: _saved ? 'Saved to History' : 'Save Analysis',
              icon: _saved ? Icons.check : Icons.bookmark_border,
              variant:
                  _saved ? AppButtonVariant.outline : AppButtonVariant.primary,
              onPressed: _saved ? null : _save,
            ),
            const SizedBox(height: AppSpacing.sm),
            AppButton(
              label: 'Export PDF',
              icon: Icons.picture_as_pdf_outlined,
              variant: AppButtonVariant.outline,
              loading: _busy == 'export',
              onPressed: _busy == null ? _exportPdf : null,
            ),
            const SizedBox(height: AppSpacing.sm),
            AppButton(
              label: 'Analyze Another',
              icon: Icons.add,
              variant: AppButtonVariant.ghost,
              onPressed: () => Navigator.of(context)
                  .pushReplacementNamed(AppRoutes.upload),
            ),
          ],
        ),
      ),
    );
  }
}

