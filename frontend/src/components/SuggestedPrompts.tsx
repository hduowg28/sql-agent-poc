import React from 'react';
import { Sparkles, ShoppingBag, TrendingUp, Users, Search } from 'lucide-react';

interface SuggestedPromptsProps {
  onSelectPrompt: (prompt: string) => void;
}

const SAMPLE_PROMPTS = [
  {
    icon: <ShoppingBag size={18} style={{ color: '#8b5cf6' }} />,
    title: 'Liệt kê 5 đơn hàng mới nhất',
    subtitle: 'Truy vấn chi tiết đơn hàng và ngày tạo',
  },
  {
    icon: <TrendingUp size={18} style={{ color: '#10b981' }} />,
    title: 'Top 5 sản phẩm bán chạy nhất',
    subtitle: 'Tính theo tổng số lượng bán ra',
  },
  {
    icon: <Users size={18} style={{ color: '#3b82f6' }} />,
    title: 'Thống kê số lượng khách hàng theo thành phố',
    subtitle: 'Gom nhóm và đếm số lượng khách',
  },
  {
    icon: <Search size={18} style={{ color: '#f59e0b' }} />,
    title: 'Tổng doanh thu tháng gần nhất là bao nhiêu?',
    subtitle: 'Tính tổng tiền các hóa đơn thành công',
  },
];

export const SuggestedPrompts: React.FC<SuggestedPromptsProps> = ({ onSelectPrompt }) => {
  return (
    <div className="welcome-container">
      <div className="welcome-icon">
        <Sparkles size={32} color="#ffffff" />
      </div>

      <h1 className="welcome-title">Hỏi đáp dữ liệu với SQL Agent</h1>
      <p className="welcome-subtitle">
        Nhập câu hỏi bằng tiếng Việt tự nhiên. AI sẽ tự động sinh câu lệnh SQL, truy vấn CSDL và trả về câu trả lời chính xác.
      </p>

      <div className="prompts-grid">
        {SAMPLE_PROMPTS.map((item, index) => (
          <div
            key={index}
            className="prompt-card"
            onClick={() => onSelectPrompt(item.title)}
          >
            <div>{item.icon}</div>
            <div>
              <div style={{ fontWeight: 600, color: '#f3f4f6' }}>{item.title}</div>
              <div style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.15rem' }}>
                {item.subtitle}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
