import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_dimensions.dart';
import '../../core/theme/app_typography.dart';
import '../../core/utils/context_ext.dart';
import '../../features/history/history_controller.dart';
import '../../navigation/app_routes.dart';
import '../../repositories/history_repository.dart';
import '../../widgets/app_button.dart';
import '../../widgets/app_card.dart';
import '../../widgets/fade_in.dart';
import '../../widgets/history_tile.dart';
import '../../widgets/section_header.dart';
import '../../widgets/skeleton.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      if (mounted) context.read<HistoryController>().load();
    });
  }

  void _openReport(String id) async {
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: CustomScrollView(
          slivers: [
            SliverAppBar(
              backgroundColor: context.colors.background,
              pinned: true,
              title: Text(
                'Chai AI',
                style: AppTypography.title(context.colors.textPrimary),
              ),
              actions: [
                IconButton(
                  tooltip: 'Settings',
                  icon: const Icon(Icons.settings_outlined),
                  onPressed: () =>
                      Navigator.of(context).pushNamed(AppRoutes.settings),
                ),
              ],
            ),
            SliverPadding(
              padding: const EdgeInsets.all(AppSpacing.lg),
              sliver: SliverList.list(
                children: [
                  _UploadHero(onTap: () {
                    Navigator.of(context).pushNamed(AppRoutes.upload);
                  }),
                  const SizedBox(height: AppSpacing.xl),
                  const _QuickActions(),
                  const SizedBox(height: AppSpacing.xl),
                  SectionHeader(
                    title: 'Recent Analyses',
                    subtitle: 'Your latest authenticity checks',
                    trailing: TextButton(
                      onPressed: () =>
                          Navigator.of(context).pushNamed(AppRoutes.history),
                      child: const Text('View all'),
                    ),
                  ),
                  const SizedBox(height: AppSpacing.md),
                  _RecentAnalyses(onOpen: _openReport),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _UploadHero extends StatelessWidget {
  final VoidCallback onTap;

  const _UploadHero({required this.onTap});

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return FadeIn(
      child: AppCard(
        padding: EdgeInsets.zero,
        onTap: onTap,
        child: Container(
          padding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.lg,
            vertical: AppSpacing.xl,
          ),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(AppRadius.lg),
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                colors.accent.withValues(alpha: 0.16),
                colors.surface.withValues(alpha: 0.4),
              ],
            ),
          ),
          child: Column(
            children: [
              Container(
                width: 64,
                height: 64,
                decoration: BoxDecoration(
                  color: colors.accent.withValues(alpha: 0.16),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: colors.accent.withValues(alpha: 0.35),
                  ),
                ),
                child: Icon(Icons.image_search, size: 30, color: colors.accent),
              ),
              const SizedBox(height: AppSpacing.md),
              Text(
                'Analyze an image',
                style: AppTypography.title(colors.textPrimary),
              ),
              const SizedBox(height: AppSpacing.xs),
              Text(
                'Upload to check if it is original, edited, or AI-generated.',
                textAlign: TextAlign.center,
                style: AppTypography.caption(colors.textSecondary),
              ),
              const SizedBox(height: AppSpacing.lg),
              AppButton(
                label: 'Start Analysis',
                icon: Icons.arrow_forward,
                onPressed: onTap,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _QuickActions extends StatelessWidget {
  const _QuickActions();

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    final actions = [
      (
        label: 'Analyze Image',
        icon: Icons.image_search,
        route: AppRoutes.upload,
      ),
      (
        label: 'Compare Images',
        icon: Icons.compare,
        route: AppRoutes.compare,
      ),
      (
        label: 'History',
        icon: Icons.history,
        route: AppRoutes.history,
      ),
      (
        label: 'Settings',
        icon: Icons.settings_outlined,
        route: AppRoutes.settings,
      ),
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SectionHeader(title: 'Quick Actions'),
        const SizedBox(height: AppSpacing.md),
        GridView.count(
          crossAxisCount: 2,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          mainAxisSpacing: AppSpacing.md,
          crossAxisSpacing: AppSpacing.md,
          childAspectRatio: 1.5,
          children: [
            for (final a in actions)
              FadeIn(
                child: AppCard(
                  padding: const EdgeInsets.all(AppSpacing.md),
                  onTap: () => Navigator.of(context).pushNamed(a.route),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(a.icon, size: 26, color: colors.accent),
                      const SizedBox(height: AppSpacing.sm),
                      Text(
                        a.label,
                        style: AppTypography.label(colors.textPrimary),
                      ),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ],
    );
  }
}

class _RecentAnalyses extends StatelessWidget {
  final void Function(String id) onOpen;

  const _RecentAnalyses({required this.onOpen});

  @override
  Widget build(BuildContext context) {
    final controller = context.watch<HistoryController>();

    if (controller.loading) return const HistoryListSkeleton();

    final recent = controller.items.take(5).toList();
    if (recent.isEmpty) {
      return AppCard(
        child: Column(
          children: [
            Icon(
              Icons.history,
              size: 32,
              color: context.colors.textTertiary,
            ),
            const SizedBox(height: AppSpacing.sm),
            Text(
              'No analyses yet',
              style: AppTypography.label(context.colors.textSecondary),
            ),
            const SizedBox(height: AppSpacing.xs),
            Text(
              'Run your first scan to see it here.',
              style: AppTypography.caption(context.colors.textTertiary),
            ),
          ],
        ),
      );
    }

    return Column(
      children: [
        for (var i = 0; i < recent.length; i++)
          FadeIn(
            delayMs: i * 70,
            child: HistoryTile(
              item: recent[i],
              onTap: () => onOpen(recent[i].id),
            ),
          ),
      ],
    );
  }
}
