"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import {
  getResumePref,
  setResumePref,
  getProgressStats,
  resetProgress,
  resetAllData,
  exportAllData,
  importAllData,
  type ResumePref,
  type SaveFile,
} from "@/lib/progress";

interface SettingsClientProps {
  allNodeIds: string[];
}

export default function SettingsClient({ allNodeIds }: SettingsClientProps) {
  const [resumePref, setResumePrefState] = useState<ResumePref>("ask");
  const [stats, setStats] = useState({ completed: 0, inProgress: 0, total: 0 });
  const [confirmReset, setConfirmReset] = useState<"progress" | "all" | null>(null);
  const [importError, setImportError] = useState<string | null>(null);
  const [importSuccess, setImportSuccess] = useState(false);
  const [exportDone, setExportDone] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setResumePrefState(getResumePref());
    setStats(getProgressStats(allNodeIds));
  }, [allNodeIds]);

  const handleResumePrefChange = (pref: ResumePref) => {
    setResumePref(pref);
    setResumePrefState(pref);
  };

  const handleResetProgress = () => {
    resetProgress();
    setStats(getProgressStats(allNodeIds));
    setConfirmReset(null);
  };

  const handleResetAll = () => {
    resetAllData();
    setStats(getProgressStats(allNodeIds));
    setResumePrefState("ask");
    setConfirmReset(null);
  };

  const handleExport = () => {
    const data = exportAllData();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    const date = new Date().toISOString().slice(0, 10);
    a.href = url;
    a.download = `aiops-roadmap-save-${date}.json`;
    a.click();
    URL.revokeObjectURL(url);
    setExportDone(true);
    setTimeout(() => setExportDone(false), 2000);
  };

  const handleImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    setImportError(null);
    setImportSuccess(false);
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 1024 * 1024) {
      setImportError("文件过大（最大 1MB）");
      return;
    }

    const reader = new FileReader();
    reader.onload = () => {
      try {
        const data = JSON.parse(reader.result as string) as SaveFile;
        if (data.version !== 1 || !data.data) {
          setImportError("存档文件格式无效");
          return;
        }
        importAllData(data);
        setStats(getProgressStats(allNodeIds));
        setResumePrefState(getResumePref());
        setImportSuccess(true);
        setTimeout(() => setImportSuccess(false), 3000);
      } catch {
        setImportError("无法解析文件，请确认是有效的存档文件。");
      }
    };
    reader.readAsText(file);
    // Reset input so the same file can be re-imported
    e.target.value = "";
  };

  const sectionClass =
    "rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-6";
  const labelClass = "text-sm font-bold uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-4";

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <div className="border-b border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
        <div className="max-w-2xl mx-auto px-4 py-4 flex items-center gap-4">
          <Link
            href="/"
            className="px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
          >
            ← 返回
          </Link>
          <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">
            设置
          </h1>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-8 space-y-6">
        {/* Resume behavior */}
        <div className={sectionClass}>
          <h2 className={labelClass}>续学行为</h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            当你再次打开本页时，是否提示回到上次浏览的主题？
          </p>
          <div className="space-y-2">
            {([
              ["ask", "每次都询问"],
              ["always", "总是自动续学"],
              ["never", "不再询问"],
            ] as const).map(([value, label]) => (
              <label
                key={value}
                className="flex items-center gap-3 p-3 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors"
              >
                <input
                  type="radio"
                  name="resumePref"
                  value={value}
                  checked={resumePref === value}
                  onChange={() => handleResumePrefChange(value)}
                  className="w-4 h-4 text-blue-600"
                />
                <span className="text-sm text-gray-800 dark:text-gray-200">{label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Progress */}
        <div className={sectionClass}>
          <h2 className={labelClass}>进度</h2>
          <div className="flex gap-6 mb-5">
            <div>
              <p className="text-2xl font-bold text-green-600 dark:text-green-400">{stats.completed}</p>
              <p className="text-xs text-gray-500">已完成</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{stats.inProgress}</p>
              <p className="text-xs text-gray-500">进行中</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-600 dark:text-gray-400">{stats.total}</p>
              <p className="text-xs text-gray-500">主题总数</p>
            </div>
          </div>

          {confirmReset === "progress" ? (
            <div className="flex items-center gap-2">
              <span className="text-sm text-red-600 dark:text-red-400">确定重置所有进度？</span>
              <button
                onClick={handleResetProgress}
                className="px-3 py-1.5 rounded-lg bg-red-600 text-white text-sm font-medium hover:bg-red-700 transition-colors"
              >
                确认
              </button>
              <button
                onClick={() => setConfirmReset(null)}
                className="px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              >
                取消
              </button>
            </div>
          ) : (
            <button
              onClick={() => setConfirmReset("progress")}
              className="px-4 py-2 rounded-xl border border-red-200 dark:border-red-800 text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors"
            >
              重置进度
            </button>
          )}
        </div>

        {/* Save / Load */}
        <div className={sectionClass}>
          <h2 className={labelClass}>存档 / 读取</h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            将你的进度与设置导出为文件，或从之前的存档导入。
          </p>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={handleExport}
              className="px-4 py-2 rounded-xl bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 transition-colors"
            >
              {exportDone ? "已下载！" : "导出到文件"}
            </button>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="px-4 py-2 rounded-xl border border-gray-200 dark:border-gray-700 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            >
              从文件导入
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".json"
              onChange={handleImport}
              className="hidden"
            />
          </div>
          {importError && (
            <p className="mt-3 text-sm text-red-600 dark:text-red-400">{importError}</p>
          )}
          {importSuccess && (
            <p className="mt-3 text-sm text-green-600 dark:text-green-400">导入成功！</p>
          )}
        </div>

        {/* Danger zone */}
        <div className={`${sectionClass} border-red-200 dark:border-red-900`}>
          <h2 className="text-sm font-bold uppercase tracking-wider text-red-500 dark:text-red-400 mb-4">
            重置全部
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            这将清除所有进度、偏好、展开的节点和视图状态，且无法撤销。
          </p>
          {confirmReset === "all" ? (
            <div className="flex items-center gap-2">
              <span className="text-sm text-red-600 dark:text-red-400">确定吗？</span>
              <button
                onClick={handleResetAll}
                className="px-3 py-1.5 rounded-lg bg-red-600 text-white text-sm font-medium hover:bg-red-700 transition-colors"
              >
                是的，重置全部
              </button>
              <button
                onClick={() => setConfirmReset(null)}
                className="px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              >
                取消
              </button>
            </div>
          ) : (
            <button
              onClick={() => setConfirmReset("all")}
              className="px-4 py-2 rounded-xl bg-red-600 text-white text-sm font-semibold hover:bg-red-700 transition-colors"
            >
              重置全部
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
