import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

enum AppLanguage {
  english('English'),
  placeholder('More languages coming soon');

  final String label;
  const AppLanguage(this.label);
}

/// App-wide preferences: theme, language, onboarding state and the (future)
/// backend endpoint. Persisted locally; screens consume this via Provider.
class SettingsService extends ChangeNotifier {
  static const String _themeKey = 'chai_theme_mode';
  static const String _onboardKey = 'chai_onboarding_seen';
  static const String _endpointKey = 'chai_backend_endpoint';

  ThemeMode _themeMode = ThemeMode.dark;
  final AppLanguage _language = AppLanguage.english;
  String _endpoint = 'http://localhost:8000';
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
    _endpoint = prefs.getString(_endpointKey) ?? _endpoint;
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
    _endpoint = value;
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_endpointKey, value);
  }
}
