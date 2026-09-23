import { useState } from "react";
import { getDistrict } from "../data/districts";
import OperationalCalendarModal from "./OperationalCalendarModal";

const MOCK_REQUESTS = [
  { id: 1, from: "Kenji Watanabe", zone: "E", resource: "Medical personnel" },
  { id: 2, from: "Aiko Sato", zone: "W", resource: "Water rations" },
];

function TransferRequestCard({ request, onApprove, onDeny }) {
  const zone = getDistrict(request.zone);

  return (
    <div className="rounded-md border border-gray-200 bg-white p-3 dark:border-gray-700 dark:bg-gray-800">
      <p className="mb-2 text-base text-[#B36B00] dark:text-[#FFC966]">
        Approve or deny incoming transfer requests
      </p>
      <div className="flex items-center justify-between gap-2">
        <p className="text-base text-gray-800 dark:text-gray-200">
          From: <span className="font-medium">{request.from}</span>,{" "}
          {zone?.name ?? request.zone}
          <br />
          {request.resource}
        </p>
        <div className="flex shrink-0 gap-2">
          <button
            type="button"
            onClick={() => onDeny?.(request.id)}
            aria-label="Deny request"
            className="flex h-7 w-7 items-center justify-center rounded-full text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/40"
          >
            ✕
          </button>
          <button
            type="button"
            onClick={() => onApprove?.(request.id)}
            aria-label="Approve request"
            className="flex h-7 w-7 items-center justify-center rounded-full text-green-600 hover:bg-green-50 dark:text-green-400 dark:hover:bg-green-900/40"
          >
            ✓
          </button>
        </div>
      </div>
    </div>
  );
}

export default function NotificationsPanel() {
  const [calendarOpen, setCalendarOpen] = useState(false);

  return (
    <div className="flex h-[80vh] flex-col overflow-hidden rounded-lg border border-[#FBD98A] shadow-sm dark:border-gray-700">
      <h2 className="bg-white border-b border-[#FBD98A] px-4 py-3 text-center text-xl font-semibold text-gray-900 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100">
        Notifs
      </h2>

      <div className="relative flex-1 overflow-y-auto bg-[#fff9ea] dark:bg-[#3a362d]">
        <div
          className="pointer-events-none absolute inset-0 bg-repeat-space opacity-10"
          style={{ backgroundImage: "url(/kaiju_fone.png)", backgroundSize: "40px auto" }}
          aria-hidden="true"
        />
        <div className="relative space-y-2 p-4">
          {MOCK_REQUESTS.map((request) => (
            <TransferRequestCard key={request.id} request={request} />
          ))}
        </div>
      </div>

      <button
        type="button"
        onClick={() => setCalendarOpen(true)}
        className="w-full bg-[#F47E00] dark:bg-[#F8A201] py-3 text-base font-bold text-white hover:bg-[#D98C00]"
      >
        go to Operational calendar
      </button>

      {calendarOpen && (
        <OperationalCalendarModal onClose={() => setCalendarOpen(false)} />
      )}
    </div>
  );
}
