import 'package:flutter/material.dart';

import '../core/theme/app_dimensions.dart';
import '../core/theme/app_typography.dart';
import '../core/utils/context_ext.dart';
import '../core/utils/enum_present.dart';
import '../core/utils/formatters.dart';
import '../models/verdict.dart';

/// A forensic score row: icon, label, animated value bar.
class ScoreBar extends StatefulWidget {
  final ScoreCategory category;
  final double value;

  const ScoreBar({super.key, required this.category, required this.value});

  @override
  State<ScoreBar> createState() => _ScoreBarState();
}

class _ScoreBarState extends State<ScoreBar>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final CurvedAnimation _curved;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: AppDurations.slow,
    );
    _curved = CurvedAnimation(parent: _controller, curve: AppCurves.emphaSized);
    _animation = Tween(begin: 0.0, end: widget.value).animate(_curved);
    _controller.forward();
  }

  @override
  void dispose() {
    _controller.dispose();
    _curved.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    final color = scoreColor(colors, widget.value);

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: AppSpacing.sm),
      child: Row(
        children: [
          Container(
            width: 34,
            height: 34,
            decoration: BoxDecoration(
              color: colors.surfaceMuted,
              borderRadius: BorderRadius.circular(AppRadius.sm),
            ),
            child: Icon(widget.category.icon, size: 17, color: colors.textSecondary),
          ),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      widget.category.label,
                      style: AppTypography.label(colors.textPrimary),
                    ),
                    Text(
                      AppFormatters.percentOneDecimal(widget.value),
                      style: AppTypography.label(color),
                    ),
                  ],
                ),
                const SizedBox(height: AppSpacing.sm),
                AnimatedBuilder(
                  animation: _animation,
                  builder: (context, child) {
                    return ClipRRect(
                      borderRadius: BorderRadius.circular(AppRadius.pill),
                      child: LinearProgressIndicator(
                        value: _animation.value,
                        minHeight: 5,
                        backgroundColor: colors.surfaceMuted,
                        valueColor: AlwaysStoppedAnimation(color),
                      ),
                    );
                  },
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
