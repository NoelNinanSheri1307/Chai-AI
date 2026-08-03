import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_dimensions.dart';
import '../../core/theme/app_typography.dart';
import '../../core/utils/context_ext.dart';
import '../../navigation/app_routes.dart';
import '../../services/settings_service.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1300),
    )..forward();
    _scheduleNavigation();
  }

  Future<void> _scheduleNavigation() async {
    await Future<void>.delayed(const Duration(milliseconds: 1900));
    if (!mounted) return;

    final settings = context.read<SettingsService>();
    var tries = 0;
    while (!settings.ready && tries < 50) {
      await Future<void>.delayed(const Duration(milliseconds: 100));
      if (!mounted) return;
      tries++;
    }

    if (!mounted) return;
    Navigator.of(context).pushReplacementNamed(
      settings.onboardingSeen ? AppRoutes.home : AppRoutes.onboarding,
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return Scaffold(
      backgroundColor: colors.background,
      body: Center(
        child: FadeTransition(
          opacity: CurvedAnimation(
            parent: _controller,
            curve: const Interval(0.0, 0.7, curve: Curves.easeOut),
          ),
          child: ScaleTransition(
            scale: Tween<double>(begin: 0.86, end: 1.0).animate(
              CurvedAnimation(
                parent: _controller,
                curve: const Interval(0.1, 1.0, curve: Curves.easeOutCubic),
              ),
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                ClipRRect(
                  borderRadius: BorderRadius.circular(AppRadius.xl),
                  child: Image.asset(
                    'assets/ChaiAILogo.png',
                    width: 96,
                    height: 96,
                    fit: BoxFit.cover,
                  ),
                ),
                const SizedBox(height: AppSpacing.lg),
                Text(
                  'Chai AI',
                  style: AppTypography.display(colors.textPrimary),
                ),
                const SizedBox(height: AppSpacing.sm),
                Text(
                  'Image Authenticity · Forensic Analysis',
                  style: AppTypography.caption(colors.textTertiary),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
