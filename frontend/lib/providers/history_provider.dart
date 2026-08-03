import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/history_item_model.dart';

class HistoryProvider extends ChangeNotifier {
  List<HistoryItem> _history = [];

  List<HistoryItem> get history => _history;

  HistoryProvider() {
    _loadHistory();
  }

  Future<void> addHistoryItem(HistoryItem item) async {
    _history.insert(0, item);
    await _saveHistory();
    notifyListeners();
  }

  Future<void> removeHistoryItem(String id) async {
    _history.removeWhere((item) => item.id == id);
    await _saveHistory();
    notifyListeners();
  }

  Future<void> clearHistory() async {
    _history.clear();
    await _saveHistory();
    notifyListeners();
  }

  Future<void> _saveHistory() async {
    final prefs = await SharedPreferences.getInstance();
    final List<String> encoded = _history.map((item) => item.toJson()).toList();
    await prefs.setStringList("history_items", encoded);
  }

  Future<void> _loadHistory() async {
    final prefs = await SharedPreferences.getInstance();
    final List<String>? stored = prefs.getStringList("history_items");

    if (stored != null) {
      _history = stored.map((item) => HistoryItem.fromJson(item)).toList();
      notifyListeners();
    }
  }
}
