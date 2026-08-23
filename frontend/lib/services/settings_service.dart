import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../core/config/app_config.dart';

enum AppLanguage {
  english('English'),
  placeholder('More languages coming soon');

  final String label;
  const AppLanguage(this.label);
}

/// App-wide preferences: theme, language, onboarding state and the
/// backend endpoint. Persisted locally; screens consume this via Provider.
class SettingsService extends ChangeNotifier {
  static const String _themeKey = 'chai_theme_mode';
  static const String _onboardKey = 'chai_onboarding_seen';
  static const String _endpointKey = 'chai_backend_endpoint';

  ThemeMode _themeMode = ThemeMode.dark;
  final AppLanguage _language = AppLanguage.english;
  String _endpoint = AppConfig.initialApiBaseUrl;

  bool _onboardingSeen = false;
  bool _ready = false;

  ThemeMode get themeMode => _themeMode;
  AppLanguage get language => _language;
  String get endpoint => _endpoint;
  bool get onboardingSeen => _onboardingSeen;
  bool get ready => _ready;

  SettingsService() {
    _load();
  }

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    final mode = prefs.getString(_themeKey);
    if (mode != null) {
      _themeMode = ThemeMode.values.firstWhere(
        (e) => e.name == mode,
        orElse: () => ThemeMode.dark,
      );
    }
    final storedEndpoint = prefs.getString(_endpointKey);
    if (storedEndpoint != null && storedEndpoint.isNotEmpty) {
      if (AppConfig.apiBaseUrlOverride.isNotEmpty &&
          (storedEndpoint == 'http://localhost:8000' ||
              storedEndpoint == 'http://127.0.0.1:8000')) {
        _endpoint = AppConfig.initialApiBaseUrl;
      } else {
        _endpoint = AppConfig.normalizeUrl(storedEndpoint);
      }
    } else {
      _endpoint = AppConfig.initialApiBaseUrl;
    }
    _onboardingSeen = prefs.getBool(_onboardKey) ?? false;
    _ready = true;
    notifyListeners();

  }

  Future<void> setThemeMode(ThemeMode mode) async {
    _themeMode = mode;
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_themeKey, mode.name);
  }

  Future<void> completeOnboarding() async {
    _onboardingSeen = true;
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_onboardKey, true);
  }

  Future<void> setEndpoint(String value) async {
    final normalized = AppConfig.normalizeUrl(value);
    _endpoint = normalized;
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_endpointKey, normalized);
  }
}

