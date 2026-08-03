import 'package:flutter/material.dart';

import '../core/theme/app_dimensions.dart';
import '../features/about/about_screen.dart';
import '../features/compare/compare_screen.dart';
import '../features/heatmap/heatmap_viewer_screen.dart';
import '../features/history/history_screen.dart';
import '../features/home/home_screen.dart';
import '../features/onboarding/onboarding_screen.dart';
import '../features/processing/processing_screen.dart';
import '../features/report/report_details_screen.dart';
import '../features/result/result_screen.dart';
import '../features/settings/settings_screen.dart';
import '../features/splash/splash_screen.dart';
import '../features/upload/upload_screen.dart';
import 'app_routes.dart';

class AppRouter {
  static Route<dynamic> onGenerateRoute(RouteSettings settings) {
    return _pageRoute(_build(settings), settings);
  }

  static Widget _build(RouteSettings settings) {
    switch (settings.name) {
      case AppRoutes.splash:
        return const SplashScreen();
      case AppRoutes.onboarding:
        return const OnboardingScreen();
      case AppRoutes.home:
        return const HomeScreen();
      case AppRoutes.upload:
        return const UploadScreen();
      case AppRoutes.processing:
        final args = settings.arguments as ProcessingArgs;
        return ProcessingScreen(args: args);
      case AppRoutes.result:
        final args = settings.arguments as ResultArgs;
        return ResultScreen(args: args);
      case AppRoutes.heatmap:
        final args = settings.arguments as HeatmapArgs;
        return HeatmapViewerScreen(args: args);
      case AppRoutes.report:
        final args = settings.arguments as ReportArgs;
        return ReportDetailsScreen(args: args);
      case AppRoutes.history:
        return const HistoryScreen();
      case AppRoutes.compare:
        return const CompareScreen();
      case AppRoutes.settings:
        return const SettingsScreen();
      case AppRoutes.about:
        return const AboutScreen();
      default:
        return const SplashScreen();
    }
  }

  static Route<dynamic> _pageRoute(Widget page, RouteSettings settings) {
    return PageRouteBuilder(
      settings: settings,
      transitionDuration: AppDurations.page,
      reverseTransitionDuration: const Duration(milliseconds: 300),
      pageBuilder: (_, _, _) => page,
      transitionsBuilder: (_, animation, _, child) {
        final curved = CurvedAnimation(
          parent: animation,
          curve: AppCurves.standard,
        );
        return FadeTransition(
          opacity: curved,
          child: SlideTransition(
            position: Tween<Offset>(
              begin: const Offset(0, 0.02),
              end: Offset.zero,
            ).animate(curved),
            child: child,
          ),
        );
      },
    );
  }
}
