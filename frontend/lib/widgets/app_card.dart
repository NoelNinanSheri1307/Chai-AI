import 'package:flutter/material.dart';

import '../core/theme/app_dimensions.dart';
import '../core/utils/context_ext.dart';

class AppCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;
  final VoidCallback? onTap;
  final bool muted;

  const AppCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(AppSpacing.lg),
    this.onTap,
    this.muted = false,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    final card = AnimatedContainer(
      duration: AppDurations.fast,
      padding: padding,
      decoration: BoxDecoration(
        color: muted ? colors.surfaceMuted : colors.surface,
        borderRadius: BorderRadius.circular(AppRadius.lg),
        border: Border.all(color: colors.border),
        boxShadow: AppShadows.card(context.isDark ? Brightness.dark : Brightness.light),
      ),
      child: child,
    );
    if (onTap == null) return card;
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(AppRadius.lg),
        child: card,
      ),
    );
  }
}
