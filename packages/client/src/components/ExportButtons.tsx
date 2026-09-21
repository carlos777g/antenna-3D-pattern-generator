/**
 * ExportButtons
 * Single responsibility: trigger downloads. Contains no mathematics and no
 * Three.js access - it receives ready-made payloads from App.
 */
export function ExportButtons({
  onSnapshot,
  onMeshJson,
  disabled,
}: {
  onSnapshot: () => void;
  onMeshJson: () => void;
  disabled: boolean;
}) {
  return (
    <div className="flex flex-col gap-2">
      <button
        type="button"
        onClick={onSnapshot}
        disabled={disabled}
        className="bg-[#2a2a44] px-3 py-2 text-xs disabled:opacity-40"
      >
        Export PNG snapshot
      </button>
      <button
        type="button"
        onClick={onMeshJson}
        disabled={disabled}
        className="bg-[#2a2a44] px-3 py-2 text-xs disabled:opacity-40"
      >
        Export mesh JSON
      </button>
    </div>
  );
}
