import 'package:flutter/material.dart';

@immutable
class AppColors extends ThemeExtension<AppColors> {
  final Color background;
  final Color surface;
  final Color surfaceMuted;
  final Color border;
  final Color borderStrong;
  final Color textPrimary;
  final Color textSecondary;
  final Color textTertiary;
  final Color accent;
  final Color accentSoft;
  final Color success;
  final Color warning;
  final Color danger;
  final Color info;

  const AppColors({
    required this.background,
    required this.surface,
    required this.surfaceMuted,
    required this.border,
    required this.borderStrong,
    required this.textPrimary,
    required this.textSecondary,
    required this.textTertiary,
    required this.accent,
    required this.accentSoft,
    required this.success,
    required this.warning,
    required this.danger,
    required this.info,
  });

  static const AppColors dark = AppColors(
    background: Color(0xFF0B0C0E),
    surface: Color(0xFF141518),
    surfaceMuted: Color(0xFF1B1D22),
    border: Color(0xFF26282F),
    borderStrong: Color(0xFF34373F),
    textPrimary: Color(0xFFEDEEF1),
    textSecondary: Color(0xFF9BA0AA),
    textTertiary: Color(0xFF626874),
    accent: Color(0xFF8B7CFF),
    accentSoft: Color(0x1F8B7CFF),
    success: Color(0xFF34D399),
    warning: Color(0xFFFBBF24),
    danger: Color(0xFFF87171),
    info: Color(0xFF60A5FA),
  );

  static const AppColors light = AppColors(
    background: Color(0xFFF6F7F9),
    surface: Color(0xFFFFFFFF),
    surfaceMuted: Color(0xFFEFF0F3),
    border: Color(0xFFE3E5EA),
    borderStrong: Color(0xFFD0D3DA),
    textPrimary: Color(0xFF0F1115),
    textSecondary: Color(0xFF585F6C),
    textTertiary: Color(0xFF98A0AD),
    accent: Color(0xFF5B4DE0),
    accentSoft: Color(0x1A5B4DE0),
    success: Color(0xFF0F9E6E),
    warning: Color(0xFFB45309),
    danger: Color(0xFFDC2626),
    info: Color(0xFF2563EB),
  );

  @override
  AppColors copyWith({
    Color? background,
    Color? surface,
    Color? surfaceMuted,
    Color? border,
    Color? borderStrong,
    Color? textPrimary,
    Color? textSecondary,
    Color? textTertiary,
    Color? accent,
    Color? accentSoft,
    Color? success,
    Color? warning,
    Color? danger,
    Color? info,
  }) {
    return AppColors(
      background: background ?? this.background,
      surface: surface ?? this.surface,
      surfaceMuted: surfaceMuted ?? this.surfaceMuted,
      border: border ?? this.border,
      borderStrong: borderStrong ?? this.borderStrong,
      textPrimary: textPrimary ?? this.textPrimary,
      textSecondary: textSecondary ?? this.textSecondary,
      textTertiary: textTertiary ?? this.textTertiary,
      accent: accent ?? this.accent,
      accentSoft: accentSoft ?? this.accentSoft,
      success: success ?? this.success,
      warning: warning ?? this.warning,
      danger: danger ?? this.danger,
      info: info ?? this.info,
    );
  }

  @override
  AppColors lerp(ThemeExtension<AppColors>? other, double t) {
    if (other is! AppColors) return this;
    return AppColors(
      background: Color.lerp(background, other.background, t)!,
      surface: Color.lerp(surface, other.surface, t)!,
      surfaceMuted: Color.lerp(surfaceMuted, other.surfaceMuted, t)!,
      border: Color.lerp(border, other.border, t)!,
      borderStrong: Color.lerp(borderStrong, other.borderStrong, t)!,
      textPrimary: Color.lerp(textPrimary, other.textPrimary, t)!,
      textSecondary: Color.lerp(textSecondary, other.textSecondary, t)!,
      textTertiary: Color.lerp(textTertiary, other.textTertiary, t)!,
      accent: Color.lerp(accent, other.accent, t)!,
      accentSoft: Color.lerp(accentSoft, other.accentSoft, t)!,
      success: Color.lerp(success, other.success, t)!,
      warning: Color.lerp(warning, other.warning, t)!,
      danger: Color.lerp(danger, other.danger, t)!,
      info: Color.lerp(info, other.info, t)!,
    );
  }
}
