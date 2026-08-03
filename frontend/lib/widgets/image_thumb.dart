import 'dart:typed_data';

import 'package:flutter/material.dart';

import '../core/theme/app_dimensions.dart';
import '../core/theme/app_typography.dart';
import '../core/utils/context_ext.dart';
import '../core/utils/enum_present.dart';
import '../models/verdict.dart';

/// Renders uploaded image bytes, or a branded gradient placeholder when no
/// bytes are available (e.g. for seeded mock history).
class ImageThumb extends StatelessWidget {
  final Uint8List? bytes;
  final Verdict? verdict;
  final String? fileName;
  final double size;
  final double radius;

  const ImageThumb({
    super.key,
    this.bytes,
    this.verdict,
    this.fileName,
    this.size = 64,
    this.radius = AppRadius.md,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    final accent = verdict?.color(colors) ?? colors.accent;

    final box = Container(
      width: size,
      height: size,
      clipBehavior: Clip.antiAlias,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(radius),
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            accent.withValues(alpha: 0.18),
            colors.surfaceMuted,
          ],
        ),
        border: Border.all(color: colors.border),
      ),
      child: bytes != null
          ? Image.memory(bytes!, fit: BoxFit.cover)
          : Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  verdict?.icon ?? Icons.image_outlined,
                  color: accent.withValues(alpha: 0.8),
                  size: size * 0.3,
                ),
                if (fileName != null && size >= 56)
                  Padding(
                    padding: const EdgeInsets.symmetric(
                      horizontal: AppSpacing.xs,
                      vertical: 2,
                    ),
                    child: Text(
                      fileName!,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: AppTypography.caption(colors.textTertiary),
                    ),
                  ),
              ],
            ),
    );

    return box;
  }
}
