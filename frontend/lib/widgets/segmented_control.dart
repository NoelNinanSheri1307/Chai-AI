import 'package:flutter/material.dart';

import '../core/theme/app_colors.dart';
import '../core/theme/app_dimensions.dart';
import '../core/theme/app_typography.dart';
import '../core/utils/context_ext.dart';

class SegmentedOption<T> {
  final T value;
  final String label;
  final IconData? icon;

  const SegmentedOption(this.value, this.label, {this.icon});
}

class SegmentedControl<T> extends StatelessWidget {
  final List<SegmentedOption<T>> options;
  final T value;
  final ValueChanged<T> onChanged;

  const SegmentedControl({
    super.key,
    required this.options,
    required this.value,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return Container(
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: colors.surfaceMuted,
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: colors.border),
      ),
      child: Row(
        children: [
          for (final option in options)
            Expanded(
              child: _segment(context, colors, option),
            ),
        ],
      ),
    );
  }

  Widget _segment(
    BuildContext context,
    AppColors colors,
    SegmentedOption<T> option,
  ) {
    final selected = option.value == value;
    return Semantics(
      button: true,
      selected: selected,
      label: option.label,
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: () => onChanged(option.value),
        child: AnimatedContainer(
          duration: AppDurations.fast,
          padding: const EdgeInsets.symmetric(vertical: 9),
          decoration: BoxDecoration(
            color: selected ? colors.surface : Colors.transparent,
            borderRadius: BorderRadius.circular(AppRadius.sm),
            boxShadow: selected
                ? AppShadows.card(context.isDark ? Brightness.dark : Brightness.light)
                : null,
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (option.icon != null) ...[
                Icon(
                  option.icon,
                  size: 15,
                  color: selected ? colors.accent : colors.textTertiary,
                ),
                const SizedBox(width: AppSpacing.sm),
              ],
              Text(
                option.label,
                style: AppTypography.label(
                  selected ? colors.textPrimary : colors.textTertiary,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
