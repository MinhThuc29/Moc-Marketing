'use client';

import React, { useState, useEffect } from 'react';
import {
  WorkflowListItem,
  TestRunResult,
} from '@moc-healthy/contracts';
import { automationApi } from '../../lib/api';
import { Button, Badge } from '@moc-healthy/ui';

interface WorkflowTestRunModalProps {
  workflow: WorkflowListItem | null;
  isOpen: boolean;
  onClose: () => void;
}

const PRESETS: Record<string, { pass: Record<string, any>; fail?: Record<string, any> }> = {
  CUSTOMER_CREATED: {
    pass: { customer_name: 'Nguyễn Hoàng Minh', customer_phone: '0912345678', customer_email: 'minh.nguyen@example.com', consent_marketing: true },
    fail: { customer_name: 'Khách không nhận tin', customer_phone: '0912345678', consent_marketing: false },
  },
  CART_ABANDONED: {
    pass: { customer_name: 'Lê Thị Thu', customer_phone: '0987654321', cart_total: 125000 },
    fail: { customer_name: 'Giỏ hàng nhỏ', customer_phone: '0987654321', cart_total: 45000 },
  },
  ORDER_COMPLETED: {
    pass: { customer_name: 'Trần Văn An', customer_phone: '0933221100', order_total: 165000 },
    fail: { customer_name: 'Đơn nhỏ', customer_phone: '0933221100', order_total: 35000 },
  },
  CUSTOMER_INACTIVE: {
    pass: { customer_name: 'Vũ Hoàng My', customer_phone: '0909090909', segment: 'AT_RISK', inactive_days: 35 },
    fail: { customer_name: 'Khách VIP đang mua', customer_phone: '0909090909', segment: 'VIP', inactive_days: 5 },
  },
  INVENTORY_EXPIRY_RISK: {
    pass: { batch_sku: 'FRUIT-TAO-NZ', days_to_expiry: 2, quantity: 18 },
    fail: { batch_sku: 'FRUIT-TAO-NZ', days_to_expiry: 15, quantity: 4 },
  },
};

export const WorkflowTestRunModal: React.FC<WorkflowTestRunModalProps> = ({
  workflow,
  isOpen,
  onClose,
}) => {
  const [contextJson, setContextJson] = useState('{}');
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<TestRunResult | null>(null);
  const [parseError, setParseError] = useState<string | null>(null);

  useEffect(() => {
    if (workflow) {
      setResult(null);
      setParseError(null);
      const preset = PRESETS[workflow.trigger_type]?.pass || {
        customer_name: 'Khách hàng Demo',
        customer_phone: '0911223344',
      };
      setContextJson(JSON.stringify(preset, null, 2));
    }
  }, [workflow]);

  if (!isOpen || !workflow) return null;

  const handleApplyPreset = (type: 'pass' | 'fail') => {
    const p = PRESETS[workflow.trigger_type]?.[type];
    if (p) {
      setContextJson(JSON.stringify(p, null, 2));
      setParseError(null);
    }
  };

  const handleRun = async () => {
    try {
      setParseError(null);
      const parsed = JSON.parse(contextJson);
      setIsRunning(true);
      const res = await automationApi.testRun(workflow.id, parsed);
      setResult(res);
    } catch (err: any) {
      if (err instanceof SyntaxError) {
        setParseError('Dữ liệu JSON ngữ cảnh không hợp lệ. Vui lòng kiểm tra lại cú pháp.');
      } else {
        setParseError(err.message || 'Không thể chạy thử nghiệm kịch bản.');
      }
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-2xl bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="p-6 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700">
                DRY-RUN SIMULATOR
              </span>
              <span className="font-mono text-xs text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                {workflow.code}
              </span>
            </div>
            <h2 className="text-lg font-bold text-slate-800 mt-1">
              Chạy Thử Nghiệm: {workflow.name}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-2 rounded-lg hover:bg-slate-100"
          >
            ✕
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-5 flex-1">
          {/* Preset Buttons */}
          <div className="flex items-center justify-between">
            <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">
              Ngữ cảnh sự kiện (Payload JSON)
            </label>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => handleApplyPreset('pass')}
                className="text-xs text-emerald-700 bg-emerald-50 hover:bg-emerald-100 px-2.5 py-1 rounded-md font-medium border border-emerald-200 transition-colors"
              >
                ✅ Dữ liệu Thỏa điều kiện
              </button>
              {PRESETS[workflow.trigger_type]?.fail && (
                <button
                  type="button"
                  onClick={() => handleApplyPreset('fail')}
                  className="text-xs text-rose-700 bg-rose-50 hover:bg-rose-100 px-2.5 py-1 rounded-md font-medium border border-rose-200 transition-colors"
                >
                  ❌ Dữ liệu Không thỏa
                </button>
              )}
            </div>
          </div>

          {/* JSON Textarea */}
          <div>
            <textarea
              rows={6}
              value={contextJson}
              onChange={(e) => setContextJson(e.target.value)}
              className="w-full font-mono text-xs p-3 bg-slate-900 text-emerald-400 rounded-xl border border-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
            {parseError && (
              <p className="text-xs text-rose-600 mt-1">{parseError}</p>
            )}
            <p className="text-[11px] text-slate-500 mt-1">
              * Dry-run giả lập hoàn toàn trong bộ nhớ; không gửi tin nhắn thật và không trừ điểm Mộc Xu.
            </p>
          </div>

          {/* Test Run Execution Result */}
          {result && (
            <div className="border border-slate-200 rounded-xl p-4 bg-slate-50 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-700">KẾT QUẢ THỰC THI GIẢ LẬP:</span>
                <Badge variant={result.status === 'SUCCESS' ? 'success' : result.status === 'CONDITIONS_UNMET' ? 'warning' : 'danger'}>
                  {result.status}
                </Badge>
              </div>

              {/* Conditions Breakdown */}
              <div>
                <p className="text-xs font-semibold text-slate-600 mb-1.5">
                  Đánh giá điều kiện ({result.conditions_passed ? 'Thỏa mãn' : 'Không thỏa mãn'}):
                </p>
                <div className="space-y-1">
                  {result.condition_evaluations?.map((ce, i) => (
                    <div
                      key={i}
                      className={`flex items-center justify-between text-xs p-2 rounded-lg border ${
                        ce.passed
                          ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                          : 'bg-rose-50 text-rose-800 border-rose-200'
                      }`}
                    >
                      <span className="font-mono">{ce.reason}</span>
                      <span className="font-bold">{ce.passed ? 'PASSED' : 'REJECTED'}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Step Outputs */}
              {result.step_runs && result.step_runs.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-slate-600 mb-1.5">
                    Các bước đã thực thi ({result.step_runs.length} bước):
                  </p>
                  <div className="space-y-2">
                    {result.step_runs.map((step) => (
                      <div key={step.step_index} className="p-3 bg-white rounded-lg border border-slate-200 text-xs">
                        <div className="flex items-center justify-between font-semibold text-slate-800 mb-1">
                          <span>Bước {step.step_index}: {step.action_type}</span>
                          <span className="text-emerald-600 font-bold text-[11px]">{step.status}</span>
                        </div>
                        {step.output && (
                          <pre className="text-[11px] font-mono text-slate-600 bg-slate-50 p-2 rounded overflow-x-auto">
                            {JSON.stringify(step.output, null, 2)}
                          </pre>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-100 bg-slate-50 flex items-center justify-end gap-3">
          <Button variant="outline" size="sm" onClick={onClose}>
            Đóng
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleRun}
            isLoading={isRunning}
          >
            🚀 Bắt đầu Chạy Thử
          </Button>
        </div>
      </div>
    </div>
  );
};
