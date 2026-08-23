import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Manages the free daily scan/upload quota for Chai AI.
class QuotaService extends ChangeNotifier {
  static const int maxDailyUploads = 10;
  static const String _countKey = 'chai_daily_upload_count';
  static const String _dateKey = 'chai_daily_upload_date';

  int _usedToday = 0;
  bool _ready = false;

  int get usedToday => _usedToday;
  int get maxUploads => maxDailyUploads;
  int get remainingUploads => (maxDailyUploads - _usedToday).clamp(0, maxDailyUploads);
  bool get hasRemainingQuota => remainingUploads > 0;
  bool get ready => _ready;

  QuotaService() {
    _load();
  }

  String _currentDayKey() {
    final now = DateTime.now().toUtc();
    return '${now.year}-${now.month.toString().padLeft(2, '0')}-${now.day.toString().padLeft(2, '0')}';
  }

  Future<void> _load() async {
    final prefs = await SharedPreferences.getInstance();
    final today = _currentDayKey();
    final savedDate = prefs.getString(_dateKey);

    if (savedDate == today) {
      _usedToday = prefs.getInt(_countKey) ?? 0;
    } else {
      // New day: reset quota counter
      _usedToday = 0;
      await prefs.setString(_dateKey, today);
      await prefs.setInt(_countKey, 0);
    }
    _ready = true;
    notifyListeners();
  }

  /// Increments the used scan count by 1. Returns false if quota is already exhausted.
  Future<bool> consumeScan() async {
    final today = _currentDayKey();
    final prefs = await SharedPreferences.getInstance();
    final savedDate = prefs.getString(_dateKey);

    if (savedDate != today) {
      _usedToday = 0;
      await prefs.setString(_dateKey, today);
    }

    if (_usedToday >= maxDailyUploads) {
      notifyListeners();
      return false;
    }

    _usedToday += 1;
    await prefs.setInt(_countKey, _usedToday);
    notifyListeners();
    return true;
  }
}
