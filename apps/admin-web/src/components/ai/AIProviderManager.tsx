'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  Button,
  Input,
  Select,
  Badge,
  DataTable,
  Column,
  EmptyState,
  StatCard,
} from '@moc-healthy/ui';
import type {
  AIProviderHealthResponse,
  AIProviderInfo,
  PromptTemplateItem,
  AITestGenerateResponse,
  AIGenerationLogItem,
} from '@moc-healthy/contracts';
import { aiApi } from '../../lib/api';

const getStatusBadge = (status: string) => {
  switch (status.toUpperCase()) {
    case 'ONLINE':
    case 'SUCCESS':
      return <Badge variant="success">🟢 Hoạt động</Badge>;
    case 'DEGRADED':
    case 'TIMEOUT':
      return <Badge variant="warning">⏳ Quá hạn (Timeout)</Badge>;
    case 'VALIDATION_ERROR':
      return <Badge variant="warning">⚠️ Lỗi Schema JSON</Badge>;
    case 'OFFLINE':
    case 'FAILED':
      return <Badge variant="danger">❌ Lỗi kết nối</Badge>;
    default:
      return <Badge variant="neutral">{status}</Badge>;
  }
};

const getCategoryLabel = (category: string) => {
  switch (category) {
    case 'COPYWRITING':
      return '✍️ Bài viết Marketing';
    case 'CONTENT_STUDIO':
      return '🎬 Kịch bản Video / Reels';
    case 'RECOMMENDATION':
      return '💡 Khuyến nghị chiến lược';
    case 'CUSTOMER_SERVICE':
      return '💬 Chăm sóc khách hàng';
    case 'PRODUCT_OPTIMIZATION':
      return '🥗 Tối ưu sản phẩm & Xả kho';
    default:
      return category;
  }
};

export const AIProviderManager: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'HEALTH' | 'TEMPLATES' | 'PLAYGROUND' | 'LOGS'>('HEALTH');

  // 1. Health & Providers State
  const [health, setHealth] = useState<AIProviderHealthResponse | null>(null);
  const [providers, setProviders] = useState<AIProviderInfo[]>([]);
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);

  // 2. Templates State
  const [templates, setTemplates] = useState<PromptTemplateItem[]>([]);
  const [isLoadingTemplates, setIsLoadingTemplates] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<PromptTemplateItem | null>(null);

  // 3. Playground State
  const [promptInput, setPromptInput] = useState('Salad Ức Gà áp chảo xốt mè rang thanh mát');
  const [selectedTemplateSlug, setSelectedTemplateSlug] = useState('');
  const [expectJson, setExpectJson] = useState(false);
  const [simulateBehavior, setSimulateBehavior] = useState('');
  const [isRunningPlayground, setIsRunningPlayground] = useState(false);
  const [playgroundResult, setPlaygroundResult] = useState<AITestGenerateResponse | null>(null);

  // 4. Logs State
  const [logs, setLogs] = useState<AIGenerationLogItem[]>([]);
  const [totalLogs, setTotalLogs] = useState(0);
  const [isLoadingLogs, setIsLoadingLogs] = useState(false);

  const [toastMsg, setToastMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // -------------------------------------------------------------
  // Data Loaders
  // -------------------------------------------------------------

  const checkHealth = useCallback(async () => {
    setIsCheckingHealth(true);
    try {
      const [h, p] = await Promise.all([aiApi.getHealth(), aiApi.listProviders()]);
      setHealth(h);
      setProviders(p);
    } catch (err: any) {
      setToastMsg({ type: 'error', text: err.message || 'Không thể kiểm tra sức khỏe AI Provider.' });
    } finally {
      setIsCheckingHealth(false);
    }
  }, []);

  const loadTemplates = useCallback(async () => {
    setIsLoadingTemplates(true);
    try {
      const res = await aiApi.listTemplates();
      setTemplates(res.items);
    } catch (err: any) {
      setToastMsg({ type: 'error', text: err.message || 'Không thể tải Prompt Templates.' });
    } finally {
      setIsLoadingTemplates(false);
    }
  }, []);

  const loadLogs = useCallback(async () => {
    setIsLoadingLogs(true);
    try {
      const res = await aiApi.listLogs({ limit: 50 });
      setLogs(res.items);
      setTotalLogs(res.total);
    } catch (err: any) {
      setToastMsg({ type: 'error', text: err.message || 'Không thể tải nhật ký AI generation.' });
    } finally {
      setIsLoadingLogs(false);
    }
  }, []);

  useEffect(() => {
    checkHealth();
  }, [checkHealth]);

  useEffect(() => {
    if (activeTab === 'TEMPLATES') loadTemplates();
    if (activeTab === 'LOGS') loadLogs();
  }, [activeTab, loadTemplates, loadLogs]);

  // -------------------------------------------------------------
  // Actions
  // -------------------------------------------------------------

  const handleRunPlayground = async () => {
    setIsRunningPlayground(true);
    setToastMsg(null);
    try {
      const res = await aiApi.testGenerate({
        prompt: promptInput,
        template_slug: selectedTemplateSlug || undefined,
        expect_json: expectJson,
        simulate_behavior: simulateBehavior || undefined,
      });
      setPlaygroundResult(res);
      if (res.success) {
        setToastMsg({ type: 'success', text: `Sinh nội dung AI thành công! Độ trễ ${res.latency_ms}ms, ${res.total_tokens} tokens.` });
      } else {
        setToastMsg({ type: 'error', text: `AI xử lý gặp vấn đề: ${res.error_message}` });
      }
    } catch (err: any) {
      setToastMsg({ type: 'error', text: err.message || 'Lỗi khi chạy Playground.' });
    } finally {
      setIsRunningPlayground(false);
    }
  };

  // -------------------------------------------------------------
  // Columns
  // -------------------------------------------------------------

  const logColumns: Column<AIGenerationLogItem>[] = [
    {
      key: 'status',
      header: 'Trạng thái',
      render: (item) => getStatusBadge(item.status),
    },
    {
      key: 'provider',
      header: 'Nhà cung cấp',
      render: (item) => (
        <div>
          <span className="font-bold text-xs text-slate-800">{item.provider_name}</span>
          <span className="text-[10px] text-slate-400 block font-mono">{item.model_name}</span>
        </div>
      ),
    },
    {
      key: 'prompt',
      header: 'Prompt (Đã lọc PII)',
      render: (item) => (
        <div className="max-w-xs">
          <p className="text-xs text-slate-800 line-clamp-2">{item.input_prompt_sanitized}</p>
          {item.prompt_slug && (
            <span className="text-[10px] text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded font-mono mt-1 inline-block">
              🏷️ {item.prompt_slug} (v{item.prompt_version})
            </span>
          )}
        </div>
      ),
    },
    {
      key: 'metrics',
      header: 'Tokens & Chi phí',
      render: (item) => (
        <div className="text-xs space-y-0.5">
          <span className="block font-medium text-slate-700">
            🔢 {item.total_tokens.toLocaleString()} tokens
          </span>
          <span className="block text-[10px] text-slate-400">
            (${item.estimated_cost_usd.toFixed(6)})
          </span>
        </div>
      ),
    },
    {
      key: 'latency',
      header: 'Độ trễ & Retry',
      render: (item) => (
        <div className="text-xs text-slate-600">
          <span>⚡ {item.latency_ms}ms</span>
          {item.retry_count > 0 && (
            <span className="block text-[10px] text-amber-600 font-bold">
              🔁 Đã thử {item.retry_count} lần
            </span>
          )}
        </div>
      ),
    },
    {
      key: 'time',
      header: 'Thời gian',
      render: (item) => (
        <span className="text-[11px] text-slate-400">
          {new Date(item.created_at).toLocaleString('vi-VN')}
        </span>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Toast Notice */}
      {toastMsg && (
        <div
          className={`p-3.5 rounded-xl border text-xs flex items-center justify-between animate-in fade-in ${
            toastMsg.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : 'bg-rose-50 border-rose-200 text-rose-800'
          }`}
        >
          <span className="font-medium">
            {toastMsg.type === 'success' ? '✓ ' : '✕ '}
            {toastMsg.text}
          </span>
          <button
            onClick={() => setToastMsg(null)}
            className="text-slate-400 hover:text-slate-700 text-sm font-bold ml-4"
          >
            ×
          </button>
        </div>
      )}

      {/* Tabs Switcher */}
      <div className="bg-white rounded-xl border border-slate-200/90 p-1.5 flex flex-wrap gap-1 shadow-2xs">
        <button
          onClick={() => setActiveTab('HEALTH')}
          className={`px-4 py-2 rounded-lg text-xs font-bold transition flex items-center gap-2 ${
            activeTab === 'HEALTH'
              ? 'bg-emerald-600 text-white shadow-xs'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <span>🏥</span>
          <span>Sức khỏe & Nhà cung cấp ({providers.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('TEMPLATES')}
          className={`px-4 py-2 rounded-lg text-xs font-bold transition flex items-center gap-2 ${
            activeTab === 'TEMPLATES'
              ? 'bg-emerald-600 text-white shadow-xs'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <span>🧩</span>
          <span>Kho Prompt Templates ({templates.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('PLAYGROUND')}
          className={`px-4 py-2 rounded-lg text-xs font-bold transition flex items-center gap-2 ${
            activeTab === 'PLAYGROUND'
              ? 'bg-emerald-600 text-white shadow-xs'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <span>🧪</span>
          <span>AI Test Sandbox & PII Masking</span>
        </button>

        <button
          onClick={() => setActiveTab('LOGS')}
          className={`px-4 py-2 rounded-lg text-xs font-bold transition flex items-center gap-2 ${
            activeTab === 'LOGS'
              ? 'bg-emerald-600 text-white shadow-xs'
              : 'text-slate-600 hover:bg-slate-100'
          }`}
        >
          <span>📜</span>
          <span>Nhật ký gọi AI & Telemetry ({totalLogs})</span>
        </button>
      </div>

      {/* =================================================================== */}
      {/* TAB 1: HEALTH & PROVIDERS */}
      {/* =================================================================== */}
      {activeTab === 'HEALTH' && (
        <div className="space-y-6">
          {/* Active Provider Health Card */}
          <div className="bg-gradient-to-br from-slate-900 to-slate-800 text-white rounded-2xl p-6 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider block">
                  Active AI Provider Indicator
                </span>
                <h3 className="text-xl font-bold mt-1 flex items-center gap-2">
                  <span>{health?.provider || 'MOCK'}</span>
                  <span className="text-sm font-normal text-slate-300">({health?.model || 'mock-gpt-healthy-v1'})</span>
                </h3>
                <p className="text-xs text-slate-400 mt-1 max-w-lg">
                  {health?.message || 'Đang sẵn sàng phục vụ các yêu cầu sinh nội dung và phân tích dữ liệu.'}
                </p>
              </div>

              <div className="flex items-center gap-4">
                <div className="text-right">
                  <span className="text-xs text-slate-400 block">Độ trễ phản hồi</span>
                  <span className="text-2xl font-black text-emerald-400 font-mono">
                    {health?.latency_ms !== undefined ? `${health.latency_ms}ms` : '---'}
                  </span>
                </div>

                <Button
                  variant="primary"
                  size="sm"
                  onClick={checkHealth}
                  disabled={isCheckingHealth}
                  className="bg-emerald-600 hover:bg-emerald-500 text-xs"
                >
                  {isCheckingHealth ? 'Đang ping...' : '⚡ Ping Health'}
                </Button>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-slate-700/60 flex flex-wrap items-center gap-4 text-xs text-slate-300">
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                Trạng thái: <strong>{health?.status || 'ONLINE'}</strong>
              </span>
              <span>•</span>
              <span>
                Chế độ vận hành:{' '}
                <strong className={health?.is_mock ? 'text-purple-300' : 'text-emerald-300'}>
                  {health?.is_mock ? '🧪 Sandbox Cục Bộ (Mock Provider)' : '🚀 Live LLM API'}
                </strong>
              </span>
              <span>•</span>
              <span>
                Bảo vệ dữ liệu: <strong>🛡️ Khử PII Tự Động (Mask SĐT & Email)</strong>
              </span>
            </div>
          </div>

          {/* Supported Providers Cards */}
          <div>
            <h4 className="text-sm font-bold text-slate-800 mb-3">Các nhà cung cấp AI được tích hợp sẵn</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {providers.map((p) => (
                <div
                  key={p.type}
                  className={`bg-white rounded-xl border p-5 space-y-3 transition ${
                    p.is_active ? 'border-emerald-500 ring-2 ring-emerald-100 shadow-xs' : 'border-slate-200'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xl">
                      {p.type === 'MOCK' ? '🧪' : p.type === 'GEMINI' ? '✨' : '🧠'}
                    </span>
                    {p.is_active ? (
                      <Badge variant="success">Đang kích hoạt</Badge>
                    ) : (
                      <Badge variant="neutral">Khả dụng</Badge>
                    )}
                  </div>
                  <div>
                    <h5 className="font-bold text-xs text-slate-900">{p.name}</h5>
                    <p className="text-[11px] text-slate-400 font-mono mt-0.5">Model: {p.default_model}</p>
                  </div>
                  <p className="text-xs text-slate-600 line-clamp-3 leading-relaxed">{p.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* =================================================================== */}
      {/* TAB 2: PROMPT TEMPLATES */}
      {/* =================================================================== */}
      {activeTab === 'TEMPLATES' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-800">Kho mẫu Prompt chuẩn hóa (Prompt Templates)</h3>
              <p className="text-xs text-slate-500">
                Lưu trữ các kịch bản viết bài, chăm sóc khách hàng và kịch bản video với kiểm soát phiên bản tự động.
              </p>
            </div>
            <Button variant="outline" size="sm" onClick={loadTemplates} disabled={isLoadingTemplates}>
              Làm mới
            </Button>
          </div>

          {isLoadingTemplates ? (
            <div className="py-12 text-center text-slate-400 text-xs">Đang tải templates...</div>
          ) : templates.length === 0 ? (
            <EmptyState
              title="Chưa có Prompt Template nào"
              description="Các mẫu prompt mặc định sẽ tự động nạp khi khởi động hệ thống."
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {templates.map((tpl) => (
                <div
                  key={tpl.id}
                  className="bg-white rounded-xl border border-slate-200 p-5 space-y-3 hover:shadow-xs transition"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
                        {getCategoryLabel(tpl.category)}
                      </span>
                      <h4 className="font-bold text-sm text-slate-900 mt-2">{tpl.name}</h4>
                      <span className="text-[10px] text-slate-400 font-mono block">slug: {tpl.slug}</span>
                    </div>
                    <Badge variant="info">v{tpl.version}</Badge>
                  </div>

                  <div className="bg-slate-50 p-3 rounded-lg border border-slate-100 text-xs text-slate-700 font-mono line-clamp-3">
                    {tpl.user_prompt_template}
                  </div>

                  <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
                    <span className="text-slate-400">Biến đầu vào:</span>
                    <div className="flex flex-wrap gap-1">
                      {tpl.input_variables.map((v) => (
                        <span key={v} className="bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded text-[10px] font-mono">
                          {`{${v}}`}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* =================================================================== */}
      {/* TAB 3: PLAYGROUND & TEST SANDBOX */}
      {/* =================================================================== */}
      {activeTab === 'PLAYGROUND' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Input Panel */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-4 shadow-2xs">
            <h4 className="font-bold text-xs uppercase tracking-wider text-slate-700">
              Cấu hình thử nghiệm AI Sandbox
            </h4>

            {/* Template Select */}
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">
                Chọn Prompt Template (Tùy chọn):
              </label>
              <Select
                value={selectedTemplateSlug}
                onChange={(e) => setSelectedTemplateSlug(e.target.value)}
                options={[
                  { value: '', label: '-- Nhập Prompt Tự Do (Freeform) --' },
                  ...templates.map((t) => ({ value: t.slug, label: `${t.name} (v${t.version})` })),
                ]}
              />
            </div>

            {/* Prompt Textarea */}
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">
                Nội dung Prompt đầu vào:
              </label>
              <textarea
                value={promptInput}
                onChange={(e) => setPromptInput(e.target.value)}
                rows={4}
                className="w-full text-xs p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 font-sans leading-relaxed"
                placeholder="Nhập yêu cầu sáng tạo nội dung..."
              />
              <span className="text-[10px] text-slate-400 block mt-1">
                💡 Thử nhập số điện thoại (ví dụ 0912345678) hoặc email để quan sát cơ chế tự động che giấu thông tin nhạy cảm (PII Masking).
              </span>
            </div>

            {/* Structured JSON & Resilience Simulator Controls */}
            <div className="grid grid-cols-2 gap-3 pt-2 border-t border-slate-100">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Định dạng đầu ra:</label>
                <div className="flex items-center gap-2 mt-1">
                  <input
                    type="checkbox"
                    id="chk-json"
                    checked={expectJson}
                    onChange={(e) => setExpectJson(e.target.checked)}
                    className="rounded text-emerald-600 focus:ring-emerald-500"
                  />
                  <label htmlFor="chk-json" className="text-xs text-slate-700 cursor-pointer">
                    Ép kiểu JSON (Structured JSON)
                  </label>
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Kiểm thử sự cố (Resilience):</label>
                <Select
                  value={simulateBehavior}
                  onChange={(e) => setSimulateBehavior(e.target.value)}
                  options={[
                    { value: '', label: 'Bình thường (Thành công)' },
                    { value: 'timeout', label: '⚠️ Mô phỏng Timeout' },
                    { value: 'malformed_json', label: '⚠️ Mô phỏng JSON lỗi' },
                    { value: 'retry_success', label: '🔁 Mô phỏng Retry rồi thành công' },
                    { value: 'fail', label: '❌ Mô phỏng Provider sập (503)' },
                  ]}
                />
              </div>
            </div>

            <Button
              variant="primary"
              onClick={handleRunPlayground}
              disabled={isRunningPlayground}
              className="w-full bg-emerald-600 hover:bg-emerald-700 py-2.5 text-xs font-bold"
            >
              {isRunningPlayground ? 'Đang thực thi AI...' : '⚡ Chạy thử nghiệm AI (Run Sandbox)'}
            </Button>
          </div>

          {/* Output Panel */}
          <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-4 shadow-2xs">
            <h4 className="font-bold text-xs uppercase tracking-wider text-slate-700">
              Kết quả phản hồi & Đo lường Telemetry
            </h4>

            {playgroundResult ? (
              <div className="space-y-3">
                {/* Metrics Bar */}
                <div className="grid grid-cols-3 gap-2 bg-slate-50 p-3 rounded-lg border border-slate-100 text-center">
                  <div>
                    <span className="text-[10px] text-slate-400 block font-semibold">TỔNG TOKENS</span>
                    <span className="text-sm font-bold text-slate-800">{playgroundResult.total_tokens}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 block font-semibold">ĐỘ TRỄ</span>
                    <span className="text-sm font-bold text-emerald-600">{playgroundResult.latency_ms}ms</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 block font-semibold">CHI PHÍ ƯỚC TÍNH</span>
                    <span className="text-sm font-bold text-slate-800">${playgroundResult.estimated_cost_usd.toFixed(6)}</span>
                  </div>
                </div>

                {/* Sanitized Prompt Evidence */}
                <div>
                  <span className="text-[10px] font-bold text-slate-500 uppercase block mb-1">
                    🛡️ Prompt đã khử PII gửi tới AI:
                  </span>
                  <div className="bg-emerald-50/70 border border-emerald-200 p-2.5 rounded-lg text-xs text-emerald-900 font-mono">
                    {playgroundResult.sanitized_input}
                  </div>
                </div>

                {/* Output View */}
                <div>
                  <span className="text-[10px] font-bold text-slate-500 uppercase block mb-1">
                    Phản hồi từ {playgroundResult.provider} ({playgroundResult.model}):
                  </span>
                  {playgroundResult.json_output ? (
                    <pre className="bg-slate-900 text-emerald-400 p-3 rounded-lg text-xs font-mono overflow-x-auto max-h-64">
                      {JSON.stringify(playgroundResult.json_output, null, 2)}
                    </pre>
                  ) : playgroundResult.text_output ? (
                    <div className="bg-slate-50 p-3.5 rounded-lg border border-slate-200 text-xs text-slate-800 whitespace-pre-line leading-relaxed">
                      {playgroundResult.text_output}
                    </div>
                  ) : (
                    <div className="bg-rose-50 border border-rose-200 p-3 rounded-lg text-xs text-rose-800">
                      {playgroundResult.error_message || 'Không có dữ liệu phản hồi.'}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="py-20 text-center text-slate-400 text-xs italic">
                Nhấn "Chạy thử nghiệm AI" để xem kết quả và số liệu tiêu thụ token.
              </div>
            )}
          </div>
        </div>
      )}

      {/* =================================================================== */}
      {/* TAB 4: AUDIT LOGS */}
      {/* =================================================================== */}
      {activeTab === 'LOGS' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-800">Nhật ký các lượt gọi AI (Generation Logs)</h3>
              <p className="text-xs text-slate-500">
                Kiểm soát toàn diện số lượng tokens, chi phí USD, độ trễ và dấu vết Prompt Sanitization.
              </p>
            </div>
            <Button variant="outline" size="sm" onClick={loadLogs} disabled={isLoadingLogs}>
              Làm mới danh sách
            </Button>
          </div>

          <DataTable<AIGenerationLogItem>
            data={logs}
            columns={logColumns}
            keyExtractor={(row) => row.id}
            isLoading={isLoadingLogs}
            emptyTitle="Chưa có lượt gọi AI nào"
            emptyDescription="Các lượt sinh nội dung từ AI Content Studio hoặc Test Sandbox sẽ được lưu tại đây."
          />
        </div>
      )}
    </div>
  );
};
