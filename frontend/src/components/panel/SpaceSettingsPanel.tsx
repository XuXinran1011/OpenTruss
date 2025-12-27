/** 空间设置面板组件 */

'use client';

import { useState, useEffect } from 'react';
import { getSpaceIntegratedHanger, setSpaceIntegratedHanger } from '@/services/spatial';
import { useToastContext } from '@/providers/ToastProvider';

interface SpaceSettingsPanelProps {
  spaceId: string;
  onClose?: () => void;
}

export function SpaceSettingsPanel({ spaceId, onClose }: SpaceSettingsPanelProps) {
  const { showToast } = useToastContext();
  const [useIntegratedHanger, setUseIntegratedHanger] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    async function loadSettings() {
      try {
        setLoading(true);
        const data = await getSpaceIntegratedHanger(spaceId);
        setUseIntegratedHanger(data.use_integrated_hanger);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : '加载空间设置失败';
        showToast(errorMessage, 'error');
      } finally {
        setLoading(false);
      }
    }

    if (spaceId) {
      loadSettings();
    }
  }, [spaceId, showToast]);

  const handleSave = async () => {
    try {
      setSaving(true);
      await setSpaceIntegratedHanger(spaceId, {
        use_integrated_hanger: useIntegratedHanger,
      });
      showToast('空间设置已保存', 'success');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '保存空间设置失败';
      showToast(errorMessage, 'error');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white border border-zinc-200 rounded-lg shadow-lg p-4 min-w-[300px]">
        <div className="flex items-center justify-center py-8">
          <div className="text-sm text-zinc-400">加载中...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-zinc-200 rounded-lg shadow-lg p-4 min-w-[300px]">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-zinc-900">空间设置</h3>
        {onClose && (
          <button
            onClick={onClose}
            className="text-zinc-400 hover:text-zinc-600"
            aria-label="关闭"
          >
            ×
          </button>
        )}
      </div>

      <div className="space-y-4">
        <div>
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={useIntegratedHanger}
              onChange={(e) => setUseIntegratedHanger(e.target.checked)}
              className="w-4 h-4 text-blue-600 border-zinc-300 rounded focus:ring-blue-500"
            />
            <span className="text-sm font-medium text-zinc-700">使用综合支吊架</span>
          </label>
          <p className="mt-1 text-xs text-zinc-500 ml-6">
            启用后，该空间内的成排管线将使用共用的综合支吊架
          </p>
        </div>

        <div className="pt-2 border-t border-zinc-200">
          <button
            onClick={handleSave}
            disabled={saving}
            className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:bg-zinc-400 disabled:cursor-not-allowed"
          >
            {saving ? '保存中...' : '保存设置'}
          </button>
        </div>
      </div>
    </div>
  );
}
