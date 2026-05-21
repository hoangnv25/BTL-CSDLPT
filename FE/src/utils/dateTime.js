/**
 * Chuyển đổi chuỗi ngày UTC từ Backend thành múi giờ Việt Nam (GMT+7) và định dạng.
 * @param {string} dateString - Chuỗi ngày (ví dụ: "2026-05-21T17:34:04" hoặc "2026-05-21T17:34:04Z")
 * @returns {string} Chuỗi ngày giờ đã chuyển đổi và định dạng vi-VN
 */
export function formatToVietnamTime(dateString) {
  if (!dateString) return '';
  
  let utcString = dateString;
  
  // Kiểm tra xem chuỗi có chỉ định múi giờ chưa (kết thúc bằng Z/z hoặc có offset +HH:MM, +HHMM, -HH:MM, -HHMM ở cuối)
  const hasTimezone = /([Zz]|[+-]\d{2}:?\d{2})$/.test(dateString);
  
  if (!hasTimezone) {
    // Nếu là naive datetime (không có timezone), ta coi là UTC và thêm 'Z' để JS parse đúng
    // Thay thế khoảng trắng thành 'T' để tăng độ tương thích cho hàm parse của JS Engine
    const formatted = dateString.replace(' ', 'T');
    utcString = formatted + 'Z';
  }
  
  const date = new Date(utcString);
  if (isNaN(date.getTime())) return dateString; // Fallback nếu chuỗi không hợp lệ
  
  return date.toLocaleString('vi-VN', {
    timeZone: 'Asia/Ho_Chi_Minh',
    hour12: false
  });
}
