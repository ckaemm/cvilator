import Link from "next/link";
import { FileSearch, Sparkles, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const features = [
  {
    icon: FileSearch,
    title: "ATS Skorlama",
    description: "CV'nizi 8 farklı kritere göre analiz edip 100 üzerinden ATS uyumluluk skoru hesaplıyoruz.",
  },
  {
    icon: Sparkles,
    title: "AI Optimizasyon",
    description: "Claude AI ile CV'nizdeki eksiklikleri tespit edip iyileştirme önerileri sunuyoruz.",
  },
  {
    icon: Download,
    title: "Tek Tıkla İndirme",
    description: "Optimize edilmiş CV'nizi tek tıkla indirin ve başvurularınızda kullanın.",
  },
];

export default function HomePage() {
  return (
    <div className="flex flex-col items-center">
      {/* Hero */}
      <section className="flex flex-col items-center py-16 text-center lg:py-24">
        <h1 className="mb-4 text-4xl font-bold tracking-tight text-text-primary sm:text-5xl lg:text-6xl">
          CV&apos;nizi ATS&apos;ye{" "}
          <span className="text-accent">Hazırlayın</span>
        </h1>
        <p className="mb-8 max-w-2xl text-lg text-slate-400">
          AI destekli analiz ile CV&apos;nizin ATS skorunu öğrenin ve optimize edin
        </p>
        <Link href="/analyze">
          <Button size="lg" className="text-base">
            Hemen Başla
          </Button>
        </Link>
      </section>

      {/* Features */}
      <section className="grid w-full gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {features.map((feature) => (
          <Card key={feature.title} className="group transition-all hover:border-slate-600">
            <CardContent className="flex flex-col items-center p-6 text-center">
              <div className="mb-4 rounded-xl bg-accent/10 p-3 transition-colors group-hover:bg-accent/20">
                <feature.icon className="h-6 w-6 text-accent" />
              </div>
              <h3 className="mb-2 text-base font-semibold text-text-primary">{feature.title}</h3>
              <p className="text-sm leading-relaxed text-slate-400">{feature.description}</p>
            </CardContent>
          </Card>
        ))}
      </section>
    </div>
  );
}
