import 'package:flutter/material.dart';

import '../core/theme/app_dimensions.dart';
import '../core/theme/app_typography.dart';
import '../core/utils/context_ext.dart';

class KeyValueRow extends StatelessWidget {
  final String label;
  final String value;
  final bool divider;

  const KeyValueRow({
    super.key,
    required this.label,
    required this.value,
    this.divider = false,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(vertical: AppSpacing.sm),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(label, style: AppTypography.caption(colors.textTertiary)),
              const SizedBox(width: AppSpacing.md),
              Flexible(
                child: Text(
                  value,
                  textAlign: TextAlign.right,
                  style: AppTypography.label(colors.textPrimary),
                ),
              ),
            ],
          ),
        ),
        if (divider)
          Divider(color: colors.border, height: 1),
      ],
    );
  }
}
