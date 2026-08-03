import 'package:flutter/material.dart';

class AppSpacing {
  static const double xs = 4;
  static const double sm = 8;
  static const double md = 16;
  static const double lg = 24;
  static const double xl = 32;
  static const double xxl = 48;
}

class AppRadius {
  static const double sm = 8;
  static const double md = 12;
  static const double lg = 16;
  static const double xl = 24;
  static const double pill = 999;
}

class AppDurations {
  static const Duration fast = Duration(milliseconds: 180);
  static const Duration base = Duration(milliseconds: 300);
  static const Duration slow = Duration(milliseconds: 500);
  static const Duration page = Duration(milliseconds: 420);
}

class AppCurves {
  static const Curve standard = Curves.easeOutCubic;
  static const Curve emphaSized = Curves.easeOutQuart;
}

class AppShadows {
  static List<BoxShadow> soft(Color color) => [
        BoxShadow(
          color: color.withValues(alpha: 0.10),
          blurRadius: 24,
          offset: const Offset(0, 8),
        ),
      ];

  static List<BoxShadow> card(Brightness brightness) => [
        BoxShadow(
          color: Colors.black.withValues(
            alpha: brightness == Brightness.dark ? 0.28 : 0.06,
          ),
          blurRadius: 20,
          offset: const Offset(0, 6),
        ),
      ];
}
