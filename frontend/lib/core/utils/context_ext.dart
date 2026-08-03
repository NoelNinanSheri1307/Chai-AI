import 'package:flutter/material.dart';

import '../theme/app_colors.dart';

extension BuildContextX on BuildContext {
  AppColors get colors =>
      Theme.of(this).extension<AppColors>() ?? AppColors.dark;

  bool get isDark => Theme.of(this).brightness == Brightness.dark;

  void showSnack(String message) {
    ScaffoldMessenger.of(this)
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(message)));
  }
}
