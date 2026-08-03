// lib/main.dart

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'providers/auth_provider.dart';
import 'core/app_theme.dart';
import 'providers/theme_provider.dart';
import 'providers/history_provider.dart';
import 'views/splash/splash_screen.dart';

void main() {
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => ThemeProvider()),
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => HistoryProvider()),
      ],
      child: const MyApp(),
    ),
  );
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    final themeProvider = Provider.of<ThemeProvider>(context);

    return MaterialApp(
      title: 'Chai AI',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: themeProvider.themeMode,
      home: const SplashScreen(),
    );
  }
}

class ThemeTestScreen extends StatelessWidget {
  const ThemeTestScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final themeProvider = Provider.of<ThemeProvider>(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Theme Toggle Test')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            ElevatedButton(
              onPressed: () {
                themeProvider.setTheme(ThemeMode.system);
              },
              child: const Text('System Mode'),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () {
                themeProvider.setTheme(ThemeMode.light);
              },
              child: const Text('Light Mode'),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () {
                themeProvider.setTheme(ThemeMode.dark);
              },
              child: const Text('Dark Mode'),
            ),
          ],
        ),
      ),
    );
  }
}
