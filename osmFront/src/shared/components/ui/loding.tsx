import { Loader2, Clock, RotateCw, RefreshCw,Hourglass } from "lucide-react";
import { useState, useEffect } from "react";
import { cn } from "@/src/shared/utils/cn"; // دالة لدمج الكلاسات إن كنت تستخدمها
import {useTranslations} from 'next-intl';
const Loading = () => {
    return (
        <div className={cn("flex flex-col items-center justify-center min-h-[300px] gap-4 bg-gray-50 rounded-lg p-8")}>
          <div className={cn("relative")}>
            <Loader2 className={cn("animate-spin h-16 w-16 text-indigo-600")} />
            <Clock className={cn("absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 h-8 w-8 text-indigo-300")} />
          </div>
          <div className={cn("text-center")}>
            <p className={cn("text-xl font-medium text-gray-800")}>Loading...</p>
            <p className={cn("text-sm text-gray-500 mt-2")}>Please wait...</p>
          </div>
        </div>
      );
};

const Loading2 = () => {
    return (
        <div className={cn("flex flex-col items-center justify-center h-64 gap-4")}>
    <div className={cn("flex gap-2")}>
      <RotateCw className={cn("animate-spin h-8 w-8 text-blue-400 animation-delay-0")} />
      <RefreshCw className={cn("animate-spin h-8 w-8 text-blue-500 animation-delay-150")} />
      <Loader2 className={cn("animate-spin h-8 w-8 text-blue-600 animation-delay-300")} />
    </div>
    <p className={cn("text-lg text-gray-700")}>Loading...</p>
  </div>
);
}

const Loading3 = () => {
  const [progress, setProgress] = useState(0);
  const t = useTranslations('loading');
  
  useEffect(() => {
    const interval = setInterval(() => {
      setProgress(prev => (prev >= 100 ? 0 : prev + 10));
    }, 300);
    
    return () => clearInterval(interval);
  }, []);

  return (
    <div className={cn("flex flex-col items-center justify-center h-72 gap-6")}>
      <div className={cn("relative")}>
        <Hourglass className={cn("h-14 w-14 text-amber-500")} />
        <Loader2 className={cn("absolute top-0 left-0 animate-spin h-14 w-14 text-amber-300 opacity-70")} />
      </div>
      
      <div className={cn("w-64 bg-gray-200 rounded-full h-2.5")}>
        <div 
          className={cn("bg-amber-500 h-2.5 rounded-full")} 
          style={{ width: `${progress}%` }}
        ></div>
      </div>
       
      <p className={cn("text-gray-700")}> {t('loading')} {progress}%</p>
      <p className={cn("text-gray-700")}> {t('message')}</p>

    </div>
  );
} 

const Loading4 = ({ message }: { message?: string }) => { 
 return (
      <div className={cn("flex items-center justify-center p-8")}>
        <div className={cn("flex flex-col items-center gap-4 bg-white p-8 rounded-xl shadow-lg")}>
          <Loader2 className={cn("animate-spin h-12 w-12 text-purple-600")} />
          <div className={cn("text-center")}>
            <h3 className={cn("text-lg font-medium text-gray-900")}>Loading...</h3>
            <p className={cn("text-sm text-gray-500 mt-1")}>{message || 'Please wait...'}</p>
          </div>
        </div>
      </div>
    );
}

const LoadingSpinner = ({ message }: { message?: string }) => {
  return (
    <div className="flex items-center justify-center px-4 py-8">
      <div className="flex flex-col items-center gap-4 bg-white dark:bg-gray-900 p-8 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 transition-all">
        <Loader2 className="animate-spin h-10 w-10 text-indigo-600 dark:text-indigo-400" />
        <div className="text-center">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Loading</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {message || 'We’re getting things ready for you...'}
          </p>
        </div>
      </div>
    </div>
  );
};



export {Loading, Loading2, Loading3, Loading4, LoadingSpinner};
