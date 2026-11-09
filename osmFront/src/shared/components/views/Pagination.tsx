"use client";
interface PaginationProps {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  pageSize?: number;
  onPageSizeChange?: (size: number) => void;
}

export function Pagination({
  page,
  totalPages,
  onPageChange,
  pageSize = 10,
  onPageSizeChange,
}: PaginationProps) {
  // 🔹 دالة لتوليد الصفحات
  const getPages = () => {
    const pages: (number | string)[] = [];

    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
    } else {
      pages.push(1);
      if (page > 3) pages.push("...");
      for (let i = Math.max(2, page - 1); i <= Math.min(totalPages - 1, page + 1); i++) {
        pages.push(i);
      }
      if (page < totalPages - 2) pages.push("...");
      pages.push(totalPages);
    }

    return pages;
  };

  return (
    <div className="flex flex-col md:flex-row items-center justify-center gap-4 mt-6">
      {/* 🔹 التحكم في عدد العناصر */}
      {onPageSizeChange && (
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">Items per page:</span>
          <select
            value={pageSize}
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
            className="border border-gray-300 rounded-md px-2 py-1 text-sm focus:ring-2 focus:ring-blue-500"
          >
            {[5, 10, 20, 50, 100].map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* 🔹 أزرار الصفحات */}
      <div className="flex items-center gap-2">
        {/* زر السابق */}
        <button
          onClick={() => onPageChange(Math.max(1, page - 1))}
          disabled={page === 1}
          className={`px-3 py-1 rounded-lg border text-sm font-medium transition 
            ${
              page === 1
                ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                : "bg-white text-gray-700 hover:bg-gray-100 border-gray-300"
            }`}
        >
          Prev
        </button>

        {/* أرقام الصفحات */}
        {getPages().map((p, idx) =>
          p === "..." ? (
            <span key={idx} className="px-2 text-gray-500">
              ...
            </span>
          ) : (
            <button
              key={p}
              onClick={() => onPageChange(Number(p))}
              className={`px-3 py-1 rounded-lg border text-sm font-medium transition 
                ${
                  p === page
                    ? "bg-blue-600 text-white border-blue-600"
                    : "bg-white text-gray-700 hover:bg-gray-100 border-gray-300"
                }`}
            >
              {p}
            </button>
          )
        )}

        {/* زر التالي */}
        <button
          onClick={() => onPageChange(Math.min(totalPages, page + 1))}
          disabled={page === totalPages}
          className={`px-3 py-1 rounded-lg border text-sm font-medium transition 
            ${
              page === totalPages
                ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                : "bg-white text-gray-700 hover:bg-gray-100 border-gray-300"
            }`}
        >
          Next
        </button>
      </div>
    </div>
  );
}
