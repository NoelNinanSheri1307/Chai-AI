import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_dimensions.dart';
import '../../core/theme/app_typography.dart';
import '../../core/utils/context_ext.dart';
import '../../models/verdict.dart';
import '../../navigation/app_routes.dart';
import '../../repositories/history_repository.dart';
import '../../widgets/empty_state.dart';
import '../../widgets/fade_in.dart';
import '../../widgets/history_tile.dart';
import '../../widgets/skeleton.dart';
import 'history_controller.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  final TextEditingController _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      if (mounted) context.read<HistoryController>().load();
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _openReport(String id) async {
    try {
      final repo = context.read<HistoryRepository>();
      final result = await repo.fetchDetail(id);
      if (!mounted) return;
      Navigator.of(context).pushNamed(
        AppRoutes.report,
        arguments: ReportArgs(result),
      );
    } catch (_) {
      if (mounted) context.showSnack('Could not open this analysis.');
    }
  }

  Future<bool> _confirmDelete() async {
    final colors = context.colors;
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete entry'),
        content: const Text(
          'This analysis will be removed from your history.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text('Delete', style: TextStyle(color: colors.danger)),
          ),
        ],
      ),
    );
    return ok == true;
  }

  Future<void> _clearAll() async {
    final colors = context.colors;
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Clear history'),
        content: const Text('All saved analyses will be removed.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text('Clear', style: TextStyle(color: colors.danger)),
          ),
        ],
      ),
    );
    if (ok == true && mounted) {
      await context.read<HistoryController>().clear();
    }
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    final controller = context.watch<HistoryController>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('History'),
        actions: [
          IconButton(
            tooltip: 'Clear history',
            icon: const Icon(Icons.delete_sweep_outlined),
            onPressed: controller.items.isEmpty ? null : _clearAll,
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(
                AppSpacing.lg,
                AppSpacing.sm,
                AppSpacing.lg,
                0,
              ),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _searchController,
                      onChanged: (v) => controller.setQuery(v),
                      decoration: const InputDecoration(
                        hintText: 'Search analyses',
                        prefixIcon: Icon(Icons.search),
                      ),
                    ),
                  ),
                  const SizedBox(width: AppSpacing.sm),
                  PopupMenuButton<HistorySort>(
                    tooltip: 'Sort',
                    icon: const Icon(Icons.sort),
                    initialValue: controller.sort,
                    onSelected: controller.setSort,
                    itemBuilder: (context) => [
                      for (final sort in HistorySort.values)
                        PopupMenuItem(
                          value: sort,
                          child: Text(sort.label),
                        ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.md),
            SizedBox(
              height: 34,
              child: ListView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
                children: [
                  _FilterChip(
                    label: 'All',
                    selected: controller.verdictFilter == null &&
                        !controller.favoritesOnly,
                    onTap: () {
                      controller.setVerdictFilter(null);
                      controller.setFavoritesOnly(false);
                    },
                  ),
                  _FilterChip(
                    label: Verdict.original.label,
                    selected: controller.verdictFilter == Verdict.original,
                    onTap: () {
                      controller.setVerdictFilter(Verdict.original);
                      controller.setFavoritesOnly(false);
                    },
                  ),
                  _FilterChip(
                    label: Verdict.aiGenerated.label,
                    selected: controller.verdictFilter == Verdict.aiGenerated,
                    onTap: () {
                      controller.setVerdictFilter(Verdict.aiGenerated);
                      controller.setFavoritesOnly(false);
                    },
                  ),

                  _FilterChip(
                    label: 'Favorites',
                    selected: controller.favoritesOnly,
                    onTap: () => controller.setFavoritesOnly(true),
                  ),
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.md),
            Expanded(
              child: controller.loading
                  ? const Padding(
                      padding: EdgeInsets.all(AppSpacing.lg),
                      child: HistoryListSkeleton(),
                    )
                  : controller.items.isEmpty
                      ? EmptyState(
                          icon: Icons.history,
                          title: 'No analyses found',
                          subtitle: 'Adjust your filters or run a new analysis.',
                          action: TextButton(
                            onPressed: () => Navigator.of(context)
                                .pushNamed(AppRoutes.upload),
                            child: const Text('Analyze an image'),
                          ),
                        )
                      : ListView.builder(
                          padding: const EdgeInsets.all(AppSpacing.lg),
                          itemCount: controller.items.length,
                          itemBuilder: (context, index) {
                            final item = controller.items[index];
                            return FadeIn(
                              delayMs: (index % 8) * 60,
                              child: Dismissible(
                                key: ValueKey(item.id),
                                direction: DismissDirection.endToStart,
                                background: Container(
                                  alignment: Alignment.centerRight,
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: AppSpacing.lg,
                                  ),
                                  decoration: BoxDecoration(
                                    color: colors.danger.withValues(alpha: 0.15),
                                    borderRadius:
                                        BorderRadius.circular(AppRadius.lg),
                                  ),
                                  child: Icon(
                                    Icons.delete_outline,
                                    color: colors.danger,
                                  ),
                                ),
                                confirmDismiss: (_) => _confirmDelete(),
                                onDismissed: (_) => context
                                    .read<HistoryController>()
                                    .remove(item.id),
                                child: HistoryTile(
                                  item: item,
                                  onTap: () => _openReport(item.id),
                                  onFavorite: () => context
                                      .read<HistoryController>()
                                      .toggleFavorite(item.id),
                                ),
                              ),
                            );
                          },
                        ),
            ),
          ],
        ),
      ),
    );
  }
}

class _FilterChip extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;

  const _FilterChip({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return Padding(
      padding: const EdgeInsets.only(right: AppSpacing.sm),
      child: ChoiceChip(
        label: Text(label),
        selected: selected,
        onSelected: (_) => onTap(),
        selectedColor: colors.accentSoft,
        backgroundColor: colors.surfaceMuted,
        showCheckmark: false,
        side: BorderSide(
          color: selected ? colors.accent : colors.border,
        ),
        labelStyle: AppTypography.label(
          selected ? colors.accent : colors.textSecondary,
        ),
      ),
    );
  }
}
