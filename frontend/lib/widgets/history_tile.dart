import 'package:flutter/material.dart';

import '../core/theme/app_dimensions.dart';
import '../core/theme/app_typography.dart';
import '../core/utils/context_ext.dart';
import '../core/utils/formatters.dart';
import '../models/history_item.dart';
import 'app_card.dart';
import 'image_thumb.dart';
import 'verdict_badge.dart';

class HistoryTile extends StatelessWidget {
  final HistoryItem item;
  final VoidCallback? onTap;
  final VoidCallback? onFavorite;
  final bool showFavorite;

  const HistoryTile({
    super.key,
    required this.item,
    this.onTap,
    this.onFavorite,
    this.showFavorite = true,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return AppCard(
      padding: const EdgeInsets.all(AppSpacing.md),
      onTap: onTap,
      child: Row(
        children: [
          ImageThumb(
            verdict: item.verdict,
            fileName: item.fileName,
            size: 56,
          ),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.fileName ?? 'Image',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: AppTypography.label(colors.textPrimary),
                ),
                const SizedBox(height: AppSpacing.xs + 2),
                Row(
                  children: [
                    VerdictBadge(
                      verdict: item.verdict,
                      confidence: item.confidence,
                    ),
                  ],
                ),
                const SizedBox(height: AppSpacing.xs + 2),
                Text(
                  AppFormatters.relative(item.timestamp),
                  style: AppTypography.caption(colors.textTertiary),
                ),
              ],
            ),
          ),
          if (showFavorite)
            IconButton(
              icon: Icon(
                item.isFavorite ? Icons.star : Icons.star_border,
                size: 20,
                color: item.isFavorite
                    ? colors.warning
                    : colors.textTertiary,
              ),
              tooltip: item.isFavorite ? 'Remove favorite' : 'Favorite',
              onPressed: onFavorite,
            ),
        ],
      ),
    );
  }
}
