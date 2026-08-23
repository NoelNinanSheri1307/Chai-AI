import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_dimensions.dart';
import '../../core/theme/app_typography.dart';
import '../../core/utils/context_ext.dart';
import '../../models/analysis_result.dart';
import '../../models/verdict.dart';
import '../../navigation/app_routes.dart';
import '../../widgets/app_card.dart';
import '../../widgets/heatmap_overlay.dart';
import '../../widgets/segmented_control.dart';
import '../../widgets/section_header.dart';

class HeatmapViewerScreen extends StatefulWidget {
  final HeatmapArgs args;

  const HeatmapViewerScreen({super.key, required this.args});

  @override
  State<HeatmapViewerScreen> createState() => _HeatmapViewerScreenState();
}

class _HeatmapViewerScreenState extends State<HeatmapViewerScreen> {
  HeatmapMode _mode = HeatmapMode.heatmap;
  double _opacity = 0.8;

  late final AnalysisResult result = widget.args.result;

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    final heatmap = result.heatmap;

    return Scaffold(
      appBar: AppBar(title: const Text('Forensic Visualizations')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(AppSpacing.lg),
          children: [
            Text(
              'Regions highlighted by Chai image analysis. Visual highlights represent localized variations in spatial frequency, noise, and lighting signals extracted during analysis.',
              style: AppTypography.caption(colors.textSecondary),
            ),
            const SizedBox(height: AppSpacing.md),
            AppCard(
              padding: EdgeInsets.zero,
              child: ClipRRect(
                borderRadius: BorderRadius.circular(AppRadius.lg),
                child: AspectRatio(
                  aspectRatio: 4 / 3,
                  child: heatmap == null
                      ? _NoHeatmap()
                      : HeatmapOverlay(
                          data: heatmap,
                          mode: _mode,
                          opacity: _opacity,
                          image: result.imageBytes != null
                              ? Image.memory(
                                  result.imageBytes!,
                                  fit: BoxFit.cover,
                                )
                              : _placeholder(colors),
                        ),
                ),
              ),
            ),
            const SizedBox(height: AppSpacing.lg),
            SegmentedControl<HeatmapMode>(
              value: _mode,
              onChanged: (v) => setState(() => _mode = v),
              options: [
                SegmentedOption(HeatmapMode.original, 'Original', icon: Icons.image_outlined),
                SegmentedOption(HeatmapMode.heatmap, 'Heatmap', icon: Icons.local_fire_department_outlined),
                SegmentedOption(HeatmapMode.split, 'Split', icon: Icons.compare),
              ],
            ),
            const SizedBox(height: AppSpacing.lg),
            SectionHeader(title: 'Opacity'),
            const SizedBox(height: AppSpacing.md),
            Row(
              children: [
                Icon(Icons.remove, color: colors.textTertiary),
                Expanded(
                  child: Slider(
                    value: _opacity,
                    min: 0.1,
                    max: 1.0,
                    onChanged: (v) => setState(() => _opacity = v),
                  ),
                ),
                Icon(Icons.add, color: colors.textTertiary),
              ],
            ),
            const SizedBox(height: AppSpacing.lg),
            if (heatmap != null && heatmap.regions.isNotEmpty) ...[
              SectionHeader(
                title: 'Highlighted Regions',
                subtitle: '${heatmap.regions.length} localized areas',
              ),
              const SizedBox(height: AppSpacing.md),
              for (final region in heatmap.regions)
                AppCard(
                  padding: const EdgeInsets.all(AppSpacing.md),
                  child: Row(
                    children: [
                      Icon(
                        Icons.gps_fixed,
                        size: 18,
                        color: colors.warning,
                      ),
                      const SizedBox(width: AppSpacing.md),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              region.label,
                              style: AppTypography.label(colors.textPrimary),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              'Signal variation ${(region.intensity * 100).round()}%',
                              style: AppTypography.caption(colors.textTertiary),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              const SizedBox(height: AppSpacing.md),
              Text(
                'Overall anomaly density: ${(heatmap.overallManipulation * 100).round()}%',
                style: AppTypography.label(colors.warning),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _placeholder(AppColors colors) {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            colors.accent.withValues(alpha: 0.18),
            colors.surfaceMuted,
          ],
        ),
      ),
      child: Center(
        child: Icon(Icons.image_outlined, size: 40, color: colors.textTertiary),
      ),
    );
  }
}

class _NoHeatmap extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.search_off, size: 40, color: colors.textTertiary),
            const SizedBox(height: AppSpacing.md),
            Text(
              'No highlighted regions detected',
              style: AppTypography.body(colors.textSecondary),
            ),
          ],
        ),
      ),
    );
  }
}

