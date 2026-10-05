#pragma once

#include <cstdint>
#include <cmath>
#include <vector>

namespace link_mini {

inline int read_varint(const std::vector<uint8_t> &data, size_t &i) {
  int value = 0;
  int shift = 0;
  while (i < data.size()) {
    const uint8_t b = data[i++];
    value |= static_cast<int>(b & 0x7F) << shift;
    if ((b & 0x80) == 0) {
      break;
    }
    shift += 7;
    if (shift > 28) {
      break;
    }
  }
  return value;
}

// Power submessage: 12 04 12 02 08 <01=aan | 25=uit>
// Alleen 0x01 / 0x25 accepteren — andere bytes in grote notifies zijn false positives.
inline bool parse_power(const std::vector<uint8_t> &data, bool &on) {
  bool found = false;
  for (size_t i = 0; i + 5 < data.size(); i++) {
    if (data[i] == 0x12 && data[i + 1] == 0x04 && data[i + 2] == 0x12 && data[i + 3] == 0x02 &&
        data[i + 4] == 0x08) {
      const uint8_t v = data[i + 5];
      if (v != 0x01 && v != 0x25) {
        continue;
      }
      // Laatste geldige match wint (korte power-notifies + state)
      on = (v == 0x01);
      found = true;
    }
  }
  return found;
}

// Color field in state-notify: … 12 05 10 <varint RGB 0xRRGGBB>
inline bool parse_color_rgb(const std::vector<uint8_t> &data, int &r, int &g, int &b) {
  static const uint8_t prefix[] = {0x12, 0x09, 0x08, 0x02, 0x12, 0x05, 0x10};
  for (size_t i = 0; i + sizeof(prefix) + 1 < data.size(); i++) {
    bool match = true;
    for (size_t j = 0; j < sizeof(prefix); j++) {
      if (data[i + j] != prefix[j]) {
        match = false;
        break;
      }
    }
    if (!match) {
      continue;
    }
    size_t pos = i + sizeof(prefix);
    const int packed = read_varint(data, pos);
    if (packed < 0 || packed > 0xFFFFFF) {
      continue;
    }
    r = (packed >> 16) & 0xFF;
    g = (packed >> 8) & 0xFF;
    b = packed & 0xFF;
    return true;
  }
  return false;
}

inline int color_distance(int r1, int g1, int b1, int r2, int g2, int b2) {
  const int dr = r1 - r2;
  const int dg = g1 - g2;
  const int db = b1 - b2;
  return dr * dr + dg * dg + db * db;
}

// Spectra programma 1–11 — benadering vaste kleuren (2–9 het betrouwbaarst)
inline int rgb_to_program(int r, int g, int b) {
  static const struct {
    int program;
    int r;
    int g;
    int bl;
  } k_map[] = {
      {2, 255, 180, 80},   // warm wit
      {3, 255, 255, 230},  // neutraal wit
      {4, 210, 230, 255},  // koud wit
      {5, 0, 190, 220},    // caribisch blauw
      {6, 0, 80, 255},     // blauw
      {7, 0, 220, 80},     // groen
      {8, 255, 0, 0},      // rood
      {9, 160, 0, 255},    // paars
  };
  int best_p = 0;
  int best_d = 999999;
  for (const auto &e : k_map) {
    const int d = color_distance(r, g, b, e.r, e.g, e.bl);
    if (d < best_d) {
      best_d = d;
      best_p = e.program;
    }
  }
  // drempel: ver genoeg van wit om geen false match
  if (best_d > 18000) {
    return 0;
  }
  return best_p;
}

inline bool is_full_state_notify(const std::vector<uint8_t> &data) { return data.size() >= 40; }

}  // namespace link_mini
