"use client";
import { lazy } from "react";
import { Suspense } from "react";
import { Loading } from "@/src/shared/components/ui/Loading";
export default function HomePage() {
  const HeroSection = lazy(() => import("@/src/shared/components/layout/home/HeroSection"));
  const FeaturesSection = lazy(() => import("@/src/shared/components/layout/home/FeaturesSection"));
  const PricingSection = lazy(() => import("@/src/shared/components/layout/home/PricingSection"));
  return (
    <div className="bg-body text-main">
      <Suspense fallback={<Loading />}>
        <HeroSection />
        <FeaturesSection />
        <PricingSection />
      </Suspense>
    </div>
  );
}


