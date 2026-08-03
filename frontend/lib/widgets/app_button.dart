import 'package:flutter/material.dart';

import '../core/theme/app_dimensions.dart';
import '../core/theme/app_typography.dart';
import '../core/utils/context_ext.dart';

enum AppButtonVariant { primary, outline, ghost, danger }

class AppButton extends StatelessWidget {
  final String label;
  final AppButtonVariant variant;
  final IconData? icon;
  final VoidCallback? onPressed;
  final bool loading;
  final bool expanded;

  const AppButton({
    super.key,
    required this.label,
    this.variant = AppButtonVariant.primary,
    this.icon,
    this.onPressed,
    this.loading = false,
    this.expanded = true,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    final isDisabled = onPressed == null || loading;

    final (bg, fg, border) = switch (variant) {
      AppButtonVariant.primary => (colors.accent, Colors.white, Colors.transparent),
      AppButtonVariant.outline => (Colors.transparent, colors.textPrimary, colors.borderStrong),
      AppButtonVariant.ghost => (Colors.transparent, colors.textSecondary, Colors.transparent),
      AppButtonVariant.danger => (colors.danger.withValues(alpha: 0.12), colors.danger, Colors.transparent),
    };

    final effectiveBg = isDisabled ? colors.surfaceMuted : bg;
    final effectiveFg = isDisabled ? colors.textTertiary : fg;

    return Semantics(
      button: true,
      enabled: !isDisabled,
      label: label,
      child: SizedBox(
        width: expanded ? double.infinity : null,
        child: Material(
          color: effectiveBg,
          borderRadius: BorderRadius.circular(AppRadius.md),
          child: InkWell(
            onTap: isDisabled ? null : onPressed,
            borderRadius: BorderRadius.circular(AppRadius.md),
            child: AnimatedContainer(
              duration: AppDurations.fast,
              curve: AppCurves.standard,
              padding: const EdgeInsets.symmetric(
                horizontal: AppSpacing.lg,
                vertical: 14,
              ),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(AppRadius.md),
                border: Border.all(color: border),
              ),
              child: Row(
                mainAxisSize: expanded ? MainAxisSize.max : MainAxisSize.min,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  if (loading)
                    SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: effectiveFg,
                      ),
                    )
                  else if (icon != null) ...[
                    Icon(icon, size: 18, color: effectiveFg),
                    const SizedBox(width: AppSpacing.sm),
                  ],
                  Text(label, style: AppTypography.button(effectiveFg)),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class AppIconButton extends StatelessWidget {
  final IconData icon;
  final String? tooltip;
  final VoidCallback? onPressed;
  final Color? color;

  const AppIconButton({
    super.key,
    required this.icon,
    this.tooltip,
    this.onPressed,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return Semantics(
      button: true,
      label: tooltip,
      child: IconButton(
        icon: Icon(icon),
        color: color ?? colors.textSecondary,
        tooltip: tooltip,
        onPressed: onPressed,
      ),
    );
  }
}
