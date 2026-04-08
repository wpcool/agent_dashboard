import React from 'react';
import { Sparkles, ArrowRight } from 'lucide-react';

interface PlaceholderPageProps {
  icon: string;
  title: string;
  description: string;
  features?: string[];
  actionText?: string;
  onAction?: () => void;
}

export const PlaceholderPage: React.FC<PlaceholderPageProps> = ({
  icon,
  title,
  description,
  features,
  actionText,
  onAction,
}) => {
  return (
    <div className="flex-1 flex items-center justify-center bg-gray-50 p-8">
      <div className="max-w-md text-center">
        <div className="text-6xl mb-6">{icon}</div>
        <h2 className="text-2xl font-bold text-gray-800 mb-3">{title}</h2>
        <p className="text-gray-500 mb-6">{description}</p>

        {features && features.length > 0 && (
          <div className="bg-white rounded-xl p-6 mb-6 text-left">
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="w-5 h-5 text-amber-500" />
              <span className="font-medium text-gray-800">即将推出</span>
            </div>
            <ul className="space-y-2">
              {features.map((feature, idx) => (
                <li key={idx} className="flex items-center gap-2 text-gray-600 text-sm">
                  <span className="w-1.5 h-1.5 bg-blue-500 rounded-full" />
                  {feature}
                </li>
              ))}
            </ul>
          </div>
        )}

        {actionText && onAction && (
          <button
            onClick={onAction}
            className="inline-flex items-center gap-2 px-6 py-3 bg-blue-500 text-white rounded-xl hover:bg-blue-600 transition-colors"
          >
            {actionText}
            <ArrowRight className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};

export default PlaceholderPage;
