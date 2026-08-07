import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_dimensions.dart';
import '../../core/theme/app_typography.dart';
import '../../core/utils/context_ext.dart';
import '../../core/utils/formatters.dart';
import '../../models/compare_result.dart';
import '../../repositories/analysis_repository.dart';
import '../../widgets/app_button.dart';
import '../../widgets/app_card.dart';
import '../../widgets/fade_in.dart';
import '../../widgets/image_thumb.dart';
import '../../widgets/section_header.dart';

class CompareScreen extends StatefulWidget {
  const CompareScreen({super.key});

  @override
  State<CompareScreen> createState() => _CompareScreenState();
}

class _CompareScreenState extends State<CompareScreen> {
  final ImagePicker _picker = ImagePicker();

  String? _nameA;
  Uint8List? _bytesA;
  String? _nameB;
  Uint8List? _bytesB;
  bool _comparing = false;
  CompareResult? _result;

  Future<void> _pick(bool isA) async {
    try {
      final picked = await _picker.pickImage(source: ImageSource.gallery);
      if (picked == null) return;
      final bytes = await picked.readAsBytes();
      if (!mounted) return;
      setState(() {
        if (isA) {
          _nameA = picked.name.isNotEmpty ? picked.name : 'Image A';
          _bytesA = bytes;
        } else {
          _nameB = picked.name.isNotEmpty ? picked.name : 'Image B';
          _bytesB = bytes;
        }
      });
    } catch (_) {
      if (mounted) context.showSnack('Could not load the image.');
    }
  }

  Future<void> _compare() async {
    if (_nameA == null || _nameB == null || _comparing) return;
    setState(() {
      _comparing = true;
      _result = null;
    });
    try {
      final repo = context.read<AnalysisRepository>();
      final result = await repo.compareImages(
        nameA: _nameA,
        nameB: _nameB,
        bytesA: _bytesA,
        bytesB: _bytesB,
      );
      if (!mounted) return;
      setState(() {
        _result = result;
        _comparing = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _comparing = false);
      context.showSnack('Comparison failed.');
    }
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    final canCompare = _nameA != null && _nameB != null;

    return Scaffold(
      appBar: AppBar(title: const Text('Compare Images')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(AppSpacing.lg),
          children: [
            Text(
              'Compare two images',
              style: AppTypography.headline(colors.textPrimary),
            ),
            const SizedBox(height: AppSpacing.sm),
            Text(
              'Detect similarities, differences and AI involvement.',
              style: AppTypography.body(colors.textSecondary),
            ),
            const SizedBox(height: AppSpacing.xl),

            LayoutBuilder(
              builder: (context, constraints) {
                final row = constraints.maxWidth >= 620;
                final slotA = _Slot(
                  title: 'Image A',
                  name: _nameA,
                  bytes: _bytesA,
                  onPick: () => _pick(true),
                );
                final slotB = _Slot(
                  title: 'Image B',
                  name: _nameB,
                  bytes: _bytesB,
                  onPick: () => _pick(false),
                );
                if (row) {
                  return Row(
                    children: [
                      Expanded(child: slotA),
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: AppSpacing.sm),
                        child: Icon(Icons.compare_arrows, color: colors.textTertiary),
                      ),
                      Expanded(child: slotB),
                    ],
                  );
                }
                return Column(
                  children: [
                    slotA,
                    const SizedBox(height: AppSpacing.md),
                    slotB,
                  ],
                );
              },
            ),

            const SizedBox(height: AppSpacing.xl),
            AppButton(
              label: 'Compare',
              icon: Icons.compare,
              loading: _comparing,
              onPressed: canCompare ? _compare : null,
            ),

            if (_result != null) ...[
              const SizedBox(height: AppSpacing.xl),
              FadeIn(child: _CompareResults(result: _result!)),
            ],
          ],
        ),
      ),
    );
  }
}

class _Slot extends StatelessWidget {
  final String title;
  final String? name;
  final Uint8List? bytes;
  final VoidCallback onPick;

  const _Slot({
    required this.title,
    required this.name,
    required this.bytes,
    required this.onPick,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return AppCard(
      padding: const EdgeInsets.all(AppSpacing.md),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(title, style: AppTypography.label(colors.textTertiary)),
              TextButton(
                onPressed: onPick,
                child: const Text('Choose'),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.sm),
          SizedBox(
            width: double.infinity,
            height: 140,
            child: Center(
              child: bytes != null
                  ? ClipRRect(
                      borderRadius: BorderRadius.circular(AppRadius.md),
                      child: Image.memory(bytes!, fit: BoxFit.cover),
                    )
                  : ImageThumb(size: 120),
            ),
          ),
          const SizedBox(height: AppSpacing.sm),
          Text(
            name ?? 'No image selected',
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: AppTypography.caption(
              name != null ? colors.textPrimary : colors.textTertiary,
            ),
          ),
        ],
      ),
    );
  }
}

class _CompareResults extends StatelessWidget {
  final CompareResult result;

  const _CompareResults({required this.result});

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SectionHeader(title: 'Comparison'),
        const SizedBox(height: AppSpacing.md),
        AppCard(
          child: Column(
            children: [
              _bar(colors, 'Similarity', result.similarity, colors.accent),
              const SizedBox(height: AppSpacing.lg),
              _bar(
                colors,
                'AI generation probability',
                result.aiProbability,
                colors.warning,
              ),
            ],
          ),
        ),
        const SizedBox(height: AppSpacing.md),
        Row(
          children: [
            Expanded(
              child: _ListCard(
                title: 'Similarities',
                icon: Icons.check_circle_outline,
                color: colors.success,
                items: result.similarities,
              ),
            ),
            const SizedBox(width: AppSpacing.md),
            Expanded(
              child: _ListCard(
                title: 'Differences',
                icon: Icons.info_outline,
                color: colors.warning,
                items: result.differences,
              ),
            ),
          ],
        ),
        if (result.manipulatedRegions.isNotEmpty) ...[
          const SizedBox(height: AppSpacing.md),
          AppCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Manipulated regions',
                  style: AppTypography.title(colors.textPrimary),
                ),
                const SizedBox(height: AppSpacing.sm),
                for (final region in result.manipulatedRegions)
                  Padding(
                    padding: const EdgeInsets.only(bottom: AppSpacing.sm),
                    child: Row(
                      children: [
                        Icon(Icons.gps_fixed, size: 16, color: colors.danger),
                        const SizedBox(width: AppSpacing.sm),
                        Expanded(
                          child: Text(
                            '${region.label} — intensity ${(region.intensity * 100).round()}%',
                            style: AppTypography.label(colors.textSecondary),
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
          ),
        ],
      ],
    );
  }

  Widget _bar(AppColors colors, String label, double value, Color color) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(label, style: AppTypography.label(colors.textSecondary)),
            Text(
              AppFormatters.percent(value),
              style: AppTypography.label(color),
            ),
          ],
        ),
        const SizedBox(height: AppSpacing.sm),
        ClipRRect(
          borderRadius: BorderRadius.circular(AppRadius.pill),
          child: LinearProgressIndicator(
            value: value,
            minHeight: 6,
            backgroundColor: colors.surfaceMuted,
            valueColor: AlwaysStoppedAnimation(color),
          ),
        ),
      ],
    );
  }
}

class _ListCard extends StatelessWidget {
  final String title;
  final IconData icon;
  final Color color;
  final List<String> items;

  const _ListCard({
    required this.title,
    required this.icon,
    required this.color,
    required this.items,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return AppCard(
      padding: const EdgeInsets.all(AppSpacing.md),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 18, color: color),
              const SizedBox(width: AppSpacing.sm),
              Text(title, style: AppTypography.label(colors.textPrimary)),
            ],
          ),
          const SizedBox(height: AppSpacing.md),
          for (final item in items)
            Padding(
              padding: const EdgeInsets.only(bottom: AppSpacing.sm),
              child: Text(
                item,
                style: AppTypography.caption(colors.textSecondary),
              ),
            ),
        ],
      ),
    );
  }
}
