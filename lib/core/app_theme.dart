import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'app_colors.dart';
import 'app_typography.dart';

class AppTheme {
  static ThemeData lightTheme =
      ThemeData(
        brightness: Brightness.light,
        scaffoldBackgroundColor: AppColors.lightBackground,
        cardColor: AppColors.lightCard,
        dividerColor: AppColors.lightBorder,
        primaryColor: AppColors.accentBlue,
        appBarTheme: const AppBarTheme(
          backgroundColor: AppColors.lightBackground,
          elevation: 0,
          foregroundColor: AppColors.lightTextPrimary,
        ),
      ).copyWith(
        textTheme: GoogleFonts.getTextTheme(
          AppTypography.currentFont,
          ThemeData.light().textTheme,
        ),
        primaryTextTheme: GoogleFonts.getTextTheme(
          AppTypography.currentFont,
          ThemeData.light().primaryTextTheme,
        ),
      );

  static ThemeData darkTheme =
      ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: AppColors.darkBackground,
        cardColor: AppColors.darkCard,
        dividerColor: AppColors.darkBorder,
        primaryColor: AppColors.accentBlue,
        appBarTheme: const AppBarTheme(
          backgroundColor: AppColors.darkBackground,
          elevation: 0,
          foregroundColor: AppColors.darkTextPrimary,
        ),
      ).copyWith(
        textTheme: GoogleFonts.getTextTheme(
          AppTypography.currentFont,
          ThemeData.dark().textTheme,
        ),
        primaryTextTheme: GoogleFonts.getTextTheme(
          AppTypography.currentFont,
          ThemeData.dark().primaryTextTheme,
        ),
      );
}
