import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'app_typography.dart';

class AppTextStyles {
  static TextStyle headingLarge(Color color) {
    return GoogleFonts.getFont(
      AppTypography.currentFont,
      fontSize: 24,
      fontWeight: FontWeight.bold,
      color: color,
    );
  }

  static TextStyle headingMedium(Color color) {
    return GoogleFonts.getFont(
      AppTypography.currentFont,
      fontSize: 18,
      fontWeight: FontWeight.w600,
      color: color,
    );
  }

  static TextStyle body(Color color) {
    return GoogleFonts.getFont(
      AppTypography.currentFont,
      fontSize: 14,
      color: color,
    );
  }

  static TextStyle scoreLarge(Color color) {
    return GoogleFonts.getFont(
      AppTypography.currentFont,
      fontSize: 40,
      fontWeight: FontWeight.bold,
      color: color,
    );
  }
}
