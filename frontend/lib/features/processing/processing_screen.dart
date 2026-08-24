import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_dimensions.dart';
import '../../core/theme/app_typography.dart';
import '../../core/utils/context_ext.dart';
import '../../navigation/app_routes.dart';
import '../../repositories/analysis_repository.dart';
import '../../widgets/app_button.dart';

class _Stage {
  final String title;
  final String description;
  final IconData icon;

  const _Stage(this.title, this.description, this.icon);
}

const List<_Stage> _stages = [
  _Stage('Preparing Image', 'Normalizing image format and dimensions', Icons.image_outlined),
  _Stage('Extracting Metadata', 'Inspecting EXIF data and capture device attributes', Icons.data_object),
  _Stage('Running Chai Forensics', 'Extracting spatial, frequency, and lighting signals', Icons.analytics_outlined),
  _Stage('External Verification', 'Querying primary authenticity signal', Icons.verified_user_outlined),
  _Stage('Synthesizing Insights', 'Calibrating multi-source decision and supporting evidence', Icons.auto_awesome_outlined),
  _Stage('Finalizing Results', 'Assembling authenticity verdict and image insights', Icons.description_outlined),
];


class ProcessingScreen extends StatefulWidget {
  final ProcessingArgs args;

  const ProcessingScreen({super.key, required this.args});

  @override
  State<ProcessingScreen> createState() => _ProcessingScreenState();
}

class _ProcessingScreenState extends State<ProcessingScreen> {
  int _completed = 0;
  bool _failed = false;
  String? _errorDetails;

  @override
  void initState() {
    super.initState();
    _run();
  }

  Future<void> _run() async {
    setState(() {
      _completed = 0;
      _failed = false;
      _errorDetails = null;
    });

    final repo = context.read<AnalysisRepository>();
    final future = repo.analyzeImage(
      imageBytes: widget.args.bytes,
      fileName: widget.args.name,
    );

    for (var i = 1; i <= _stages.length; i++) {
      await Future<void>.delayed(const Duration(milliseconds: 620));
      if (!mounted) return;
      setState(() => _completed = i);
    }

    try {
      final result = await future;
      if (!mounted) return;
      Navigator.of(context).pushReplacementNamed(
        AppRoutes.result,
        arguments: ResultArgs(result),
      );
    } catch (e, st) {
      debugPrint('====================================');
      debugPrint('CHAI AI ANALYSIS FAILED: $e');
      debugPrint('STACK TRACE: $st');
      debugPrint('====================================');
      if (!mounted) return;
      setState(() {
        _failed = true;
        _errorDetails = e.toString().replaceAll('ClientException: ', '');
      });
    }
  }


  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Analyzing'),
        automaticallyImplyLeading: false,
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(AppSpacing.lg),
          child: _failed
              ? _buildError(colors)
              : Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Forensic analysis',
                      style: AppTypography.headline(colors.textPrimary),
                    ),
                    const SizedBox(height: AppSpacing.xs),
                    Text(
                      widget.args.name,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: AppTypography.caption(colors.textTertiary),
                    ),
                    const SizedBox(height: AppSpacing.xl),
                    Expanded(
                      child: ListView.builder(
                        itemCount: _stages.length,
                        itemBuilder: (context, i) => _StageTile(
                          index: i,
                          stage: _stages[i],
                          completedCount: _completed,
                        ),
                      ),
                    ),
                    const SizedBox(height: AppSpacing.md),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(AppRadius.pill),
                      child: LinearProgressIndicator(
                        value: _completed / _stages.length,
                        minHeight: 6,
                        backgroundColor: colors.surfaceMuted,
                      ),
                    ),
                    const SizedBox(height: AppSpacing.sm),
                    Text(
                      '$_completed of ${_stages.length} stages',
                      style: AppTypography.caption(colors.textTertiary),
                    ),
                  ],
                ),
        ),
      ),
    );
  }

  Widget _buildError(AppColors colors) {
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(Icons.error_outline, size: 56, color: colors.danger),
        const SizedBox(height: AppSpacing.lg),
        Text(
          'Analysis failed',
          style: AppTypography.title(colors.textPrimary),
        ),
        const SizedBox(height: AppSpacing.sm),
        Text(
          _errorDetails ?? 'The analysis engine could not process this image.',
          textAlign: TextAlign.center,
          style: AppTypography.body(colors.textSecondary),
        ),
        const SizedBox(height: AppSpacing.xl),
        AppButton(
          label: 'Try Again',
          icon: Icons.refresh,
          onPressed: _run,
        ),
        const SizedBox(height: AppSpacing.sm),
        AppButton(
          label: 'Go Back',
          variant: AppButtonVariant.outline,
          onPressed: () => Navigator.of(context).maybePop(),
        ),
      ],
    );
  }

}

class _StageTile extends StatelessWidget {
  final int index;
  final _Stage stage;
  final int completedCount;

  const _StageTile({
    required this.index,
    required this.stage,
    required this.completedCount,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    final completed = index < completedCount;
    final active = index == completedCount;

    final icon = completed ? Icons.check_circle : stage.icon;

    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.md),
      child: AnimatedOpacity(
        duration: AppDurations.base,
        opacity: active || completed ? 1.0 : 0.45,
        child: Row(
          children: [
            AnimatedContainer(
              duration: AppDurations.base,
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: completed
                    ? colors.success.withValues(alpha: 0.15)
                    : active
                        ? colors.accentSoft
                        : colors.surfaceMuted,
                borderRadius: BorderRadius.circular(AppRadius.md),
              ),
              child: Icon(
                icon,
                size: 19,
                color: completed
                    ? colors.success
                    : active
                        ? colors.accent
                        : colors.textTertiary,
              ),
            ),
            const SizedBox(width: AppSpacing.md),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    stage.title,
                    style: AppTypography.label(colors.textPrimary),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    stage.description,
                    style: AppTypography.caption(colors.textTertiary),
                  ),
                ],
              ),
            ),
            if (active)
              SizedBox(
                width: 14,
                height: 14,
                child: CircularProgressIndicator(
                  strokeWidth: 2,
                  color: colors.accent,
                ),
              ),
          ],
        ),
      ),
    );
  }
}
