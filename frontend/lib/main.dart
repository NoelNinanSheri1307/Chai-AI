import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'core/theme/app_theme.dart';
import 'features/history/history_controller.dart';
import 'features/splash/splash_screen.dart';
import 'navigation/app_router.dart';
import 'repositories/analysis_repository.dart';
import 'repositories/api/api_analysis_repository.dart';
import 'repositories/api/api_history_repository.dart';
import 'repositories/history_repository.dart';
import 'repositories/mock/mock_report_repository.dart';
import 'repositories/report_repository.dart';
import 'services/settings_service.dart';
import 'services/share_service.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const ChaiApp());
}

class ChaiApp extends StatelessWidget {
  const ChaiApp({super.key});

  @override
  Widget build(BuildContext context) {
    final settings = SettingsService();
    return MultiProvider(
      providers: [
        // The frontend talks to the running backend over HTTP.
        // It reads from the dynamically configured endpoint in SettingsService / AppConfig.
        Provider<AnalysisRepository>(
          create: (_) => ApiAnalysisRepository(() => settings.endpoint),
        ),
        Provider<HistoryRepository>(
          create: (_) => ApiHistoryRepository(() => settings.endpoint),
        ),
        Provider<ReportRepository>(create: (_) => MockReportRepository()),

        ChangeNotifierProvider<SettingsService>(create: (_) => settings),
        ChangeNotifierProvider<HistoryController>(
          create: (ctx) => HistoryController(ctx.read<HistoryRepository>()),
        ),
        Provider(create: (_) => ShareService()),
      ],
      child: const ChaiAppRoot(),
    );
  }
}

class ChaiAppRoot extends StatelessWidget {
  const ChaiAppRoot({super.key});

  @override
  Widget build(BuildContext context) {
    final settings = context.watch<SettingsService>();
    return MaterialApp(
      title: 'Chai AI',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      darkTheme: AppTheme.dark(),
      themeMode: settings.themeMode,
      onGenerateRoute: AppRouter.onGenerateRoute,
      builder: (context, child) => MediaQuery.withClampedTextScaling(
        minScaleFactor: 0.9,
        maxScaleFactor: 1.4,
        child: child!,
      ),
      home: const SplashScreen(),
    );
  }
}
