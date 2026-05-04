import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ChevronLeft, ChevronRight, Search } from 'lucide-react';
import Navbar from '../components/layout/Navbar';
import Footer from '../components/layout/Footer';
import SearchBar from '../components/jobs/SearchBar';
import JobCategories from '../components/jobs/JobCategories';
import JobCard from '../components/jobs/JobCard';
import { getFeaturedJobs } from '../api/jobs';

// ─── Company data ─────────────────────────────────────────────────────────────

interface Company {
  name: string;
  domain: string;
  logoUrl: string; // Direct reliable SVG URL
  bg: string;
  color: string;
  label: string;
}

const FEATURED_COMPANIES: Company[] = [
  { name: 'Cognizant',      domain: 'cognizant.com',       logoUrl: 'https://commons.wikimedia.org/wiki/Special:FilePath/Cognizant_logo_2022.svg', bg: '#1a2065', color: '#fff', label: 'Cognizant' },
  { name: 'Infosys',        domain: 'infosys.com',         logoUrl: 'https://commons.wikimedia.org/wiki/Special:FilePath/Infosys_logo.svg', bg: '#007CC3', color: '#fff', label: 'Infosys' },
  { name: 'Capgemini',      domain: 'capgemini.com',       logoUrl: 'https://commons.wikimedia.org/wiki/Special:FilePath/Capgemini_201x_logo.svg', bg: '#0070AD', color: '#fff', label: 'Capgemini' },
  { name: 'LTIMindtree',    domain: 'ltimindtree.com',     logoUrl: 'https://commons.wikimedia.org/wiki/Special:FilePath/LTIMindtree_Logo.svg', bg: '#E05A1E', color: '#fff', label: 'LTIMindtree' },
  { name: 'Xoriant',        domain: 'xoriant.com',         logoUrl: 'https://t1.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://www.xoriant.com&size=128', bg: '#0d5c2e', color: '#fff', label: 'Xoriant' },
  { name: 'Intellect',      domain: 'intellectdesign.com', logoUrl: 'https://commons.wikimedia.org/wiki/Special:FilePath/Intellect_Design_Arena_Logo.png', bg: '#ff6b00', color: '#fff', label: 'intellect·' },
  { name: 'Gallagher',      domain: 'ajg.com',             logoUrl: 'https://commons.wikimedia.org/wiki/Special:FilePath/Arthur_J._Gallagher_%26_Co._logo.svg', bg: '#004b8d', color: '#fff', label: 'Gallagher' },
  { name: 'TCS',            domain: 'tcs.com',             logoUrl: 'https://commons.wikimedia.org/wiki/Special:FilePath/Tata_Consultancy_Services_Logo.svg', bg: '#1A4DA2', color: '#fff', label: 'TCS' },
  { name: 'Wipro',          domain: 'wipro.com',           logoUrl: 'https://commons.wikimedia.org/wiki/Special:FilePath/Wipro_Primary_Logo_Color_RGB.svg', bg: '#341E60', color: '#fff', label: 'Wipro' },
  { name: 'HCLTech',        domain: 'hcltech.com',         logoUrl: 'https://commons.wikimedia.org/wiki/Special:FilePath/HCLTech-new-logo.svg', bg: '#0000A0', color: '#fff', label: 'HCLTech' },
  { name: 'Tech Mahindra',  domain: 'techmahindra.com',    logoUrl: 'https://commons.wikimedia.org/wiki/Special:FilePath/Tech_Mahindra_New_Logo.svg', bg: '#C8102E', color: '#fff', label: 'Tech Mahindra' },
  { name: 'Accenture',      domain: 'accenture.com',       logoUrl: 'https://commons.wikimedia.org/wiki/Special:FilePath/Accenture_2017_logo.svg', bg: '#A100FF', color: '#fff', label: 'Accenture' },
  { name: 'IBM',            domain: 'ibm.com',             logoUrl: 'https://commons.wikimedia.org/wiki/Special:FilePath/IBM_logo.svg', bg: '#1F70C1', color: '#fff', label: 'IBM' },
  { name: 'Zomato',         domain: 'zomato.com',          logoUrl: 'https://upload.wikimedia.org/wikipedia/commons/b/bd/Zomato_Logo.svg', bg: '#E23744', color: '#fff', label: 'Zomato' },
  { name: 'Flipkart',       domain: 'flipkart.com',        logoUrl: 'https://upload.wikimedia.org/wikipedia/en/7/7a/Flipkart_logo.svg', bg: '#2874F0', color: '#fff', label: 'Flipkart' },
  { name: 'Razorpay',       domain: 'razorpay.com',        logoUrl: 'https://commons.wikimedia.org/wiki/Special:FilePath/Razorpay_logo.svg', bg: '#072654', color: '#fff', label: 'Razorpay' },
  { name: 'Swiggy',         domain: 'swiggy.com',          logoUrl: 'https://upload.wikimedia.org/wikipedia/en/1/12/Swiggy_logo.svg', bg: '#FC8019', color: '#fff', label: 'Swiggy' },
  { name: 'PhonePe',        domain: 'phonepe.com',         logoUrl: 'https://commons.wikimedia.org/wiki/Special:FilePath/PhonePe_Logo.svg', bg: '#5F259F', color: '#fff', label: 'PhonePe' },
];

const TRENDING_SKILLS = [
  'Accounting Jobs', 'Analytics Jobs', 'Animation Jobs', 'Architecture Jobs',
  'Banking Jobs', 'BPO Jobs', 'Data Science Jobs', 'Java Jobs',
  'Marketing Jobs', 'React Jobs', 'Python Jobs', 'DevOps Jobs',
];

const TRENDING_JOBS = [
  'Business Analyst Jobs', 'Digital Marketing Head Jobs', 'Engineering Manager Jobs',
  'HR Head Jobs', 'Marketing Head Jobs', 'Marketing Manager Jobs',
  'Product Manager Jobs', 'Sales Manager Jobs',
];

const VACANCY_TABS = ['Skills', 'Location', 'Industry', 'Functions', 'Roles', 'Company'] as const;
type VacancyTab = (typeof VACANCY_TABS)[number];

const VACANCY_DATA: Record<VacancyTab, string[]> = {
  Skills: [
    'Python', 'Sql', 'Java', 'Excel', 'AWS', 'Javascript', 'Sales', 'Git',
    'Azure', 'Docker', 'Kubernetes', 'Data Analysis', 'Ms Office',
    'Lead Generation', 'Power Bi', 'Gcp', 'HTML', 'Linux', 'Project Management', 'CSS',
  ],
  Location: ['Bangalore', 'Mumbai', 'Delhi', 'Hyderabad', 'Chennai', 'Pune', 'Kolkata', 'Ahmedabad', 'Noida', 'Gurugram'],
  Industry: ['IT & Software', 'Banking & Finance', 'Healthcare', 'Education', 'Retail', 'Manufacturing', 'Telecom', 'Real Estate'],
  Functions: ['Engineering', 'Sales', 'Marketing', 'HR & Admin', 'Finance', 'Operations', 'Customer Support', 'Design'],
  Roles: ['Software Engineer', 'Product Manager', 'Data Scientist', 'Business Analyst', 'UI/UX Designer', 'DevOps Engineer', 'HR Manager', 'Marketing Manager'],
  Company: ['TCS', 'Infosys', 'Wipro', 'Cognizant', 'HCL', 'Accenture', 'Capgemini', 'IBM', 'Tech Mahindra', 'L&T Infotech'],
};

// ─── CompanyLogo component ────────────────────────────────────────────────────
// Tries Clearbit first; if unavailable shows a brand-coloured badge.
// Inner 123×54 div prevents max-w/max-h resolving to the outer padded dimension.

function CompanyLogo({ company }: { company: Company }) {
  const [imgUrl, setImgUrl] = useState(company.logoUrl);
  const [failedLevel, setFailedLevel] = useState(0);

  const handleError = () => {
    if (failedLevel === 0) {
      // Fallback 1: Try Google Favicon (always reliable for domains)
      setImgUrl(`https://t1.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://${company.domain}&size=128`);
      setFailedLevel(1);
    } else {
      // Fallback 2: Colored Box
      setFailedLevel(2);
    }
  };

  return (
    <Link
      to={`/jobs?company=${encodeURIComponent(company.name)}`}
      className="shrink-0 group flex-none"
      title={company.name}
    >
      <div className="w-[155px] h-[80px] bg-white rounded-lg shadow-[0_2px_8px_rgb(0,0,0,0.08)] flex items-center justify-center overflow-hidden hover:shadow-[0_4px_12px_rgb(0,0,0,0.12)] hover:-translate-y-0.5 transition-all duration-300">
        {failedLevel < 2 ? (
          /* Padded container prevents logo from stretching to edges */
          <div className="flex items-center justify-center p-3" style={{ width: '100%', height: '100%' }}>
            <img
              src={imgUrl}
              alt={company.name}
              className="max-w-full max-h-full object-contain"
              onError={handleError}
              loading="lazy"
            />
          </div>
        ) : (
          <div
            className="w-full h-full flex items-center justify-center"
            style={{ backgroundColor: company.bg }}
          >
            <span
              className="text-sm font-bold text-center leading-tight px-3 tracking-wide"
              style={{ color: company.color }}
            >
              {company.label}
            </span>
          </div>
        )}
      </div>
    </Link>
  );
}

// ─── HorizontalScrollRow ──────────────────────────────────────────────────────

function HorizontalScrollRow({ label, items }: { label: string; items: string[] }) {
  const scrollRef = useRef<HTMLDivElement>(null);

  const scroll = (dir: 'left' | 'right') => {
    scrollRef.current?.scrollBy({ left: dir === 'left' ? -240 : 240, behavior: 'smooth' });
  };

  return (
    <div className="flex items-center gap-3 py-2">
      <span className="shrink-0 text-sm font-bold text-[#333333] min-w-[160px]">{label}</span>

      <button type="button" onClick={() => scroll('left')} aria-label="Scroll left"
        className="shrink-0 flex h-7 w-7 items-center justify-center rounded-full border border-[#e0e0e0] bg-white text-[#666666] hover:border-[#7c3aed] hover:text-[#7c3aed] transition-colors">
        <ChevronLeft className="h-4 w-4" />
      </button>

      <div ref={scrollRef} className="flex gap-2 overflow-x-auto flex-1"
        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}>
        {items.map((item) => (
          <Link key={item} to={`/jobs?q=${encodeURIComponent(item)}`}
            className="shrink-0 rounded-full border border-[#e0e0e0] bg-white px-4 py-1.5 text-sm text-[#333333] hover:border-[#7c3aed] hover:text-[#7c3aed] transition-colors whitespace-nowrap">
            {item}
          </Link>
        ))}
      </div>

      <button type="button" onClick={() => scroll('right')} aria-label="Scroll right"
        className="shrink-0 flex h-7 w-7 items-center justify-center rounded-full border border-[#e0e0e0] bg-white text-[#666666] hover:border-[#7c3aed] hover:text-[#7c3aed] transition-colors">
        <ChevronRight className="h-4 w-4" />
      </button>
    </div>
  );
}

// ─── Main Home Component ──────────────────────────────────────────────────────

export default function Home() {
  const [activeTab, setActiveTab] = useState<VacancyTab>('Skills');

  const companyScrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = companyScrollRef.current;
    if (!el) return;
    const STEP = 185; // card 160px + gap 20px + buffer 5px
    const tick = () => {
      const half = el.scrollWidth / 2;
      const next = el.scrollLeft + STEP;
      if (next >= half) {
        el.scrollTo({ left: 0, behavior: 'instant' });
      } else {
        el.scrollTo({ left: next, behavior: 'smooth' });
      }
    };
    const id = setInterval(tick, 2500);
    return () => clearInterval(id);
  }, []);

  const scrollCompanies = (dir: 'left' | 'right') => {
    companyScrollRef.current?.scrollBy({ left: dir === 'left' ? -185 : 185, behavior: 'smooth' });
  };

  const { data: featuredJobs = [], isLoading } = useQuery({
    queryKey: ['featured-jobs'],
    queryFn: () => getFeaturedJobs(6),
    staleTime: 5 * 60 * 1000,
  });

  return (
    <div className="min-h-screen flex flex-col bg-[#f5f5f5]">
      <Navbar />

      {/* ── HERO ─────────────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden pt-[60px]" style={{ background: 'linear-gradient(to bottom, #fcfaff 0%, #ffffff 100%)' }}>
        <div className="relative max-w-7xl mx-auto px-4 flex items-center justify-center" style={{ minHeight: '320px' }}>
          {/* Decorative left - Man Image */}
          <div className="absolute left-4 bottom-0 hidden xl:flex items-end h-[280px] pointer-events-none" aria-hidden="true">
            <img 
              src="/hero_man.png" 
              alt="Excited professional" 
              className="h-full object-contain"
            />
          </div>

          {/* Center content */}
          <div className="flex flex-col items-center text-center py-14 w-full max-w-3xl z-10">
            <h1 className="text-4xl md:text-[44px] font-black leading-tight mb-3" style={{ color: '#7b1fa2', letterSpacing: '-0.02em' }}>
              8,00,000+ Jobs In India
            </h1>
            <p className="text-[#1a1a2e] font-bold mb-10 text-[18px]">
              Get Hired by Top Companies
            </p>
            <div className="w-full relative z-20 shadow-[0_8px_30px_rgb(0,0,0,0.08)] rounded-full">
              <SearchBar size="lg" />
            </div>
          </div>

          {/* Decorative right - Cricket Image */}
          <div className="absolute right-4 bottom-0 hidden xl:flex items-end h-[260px] pointer-events-none" aria-hidden="true">
             <img 
              src="/hero_cricket.png" 
              alt="Cricket stumps" 
              className="h-full object-contain"
            />
          </div>
        </div>
      </section>

      {/* ── FEATURED COMPANIES ───────────────────────────────────────────── */}
      <section className="bg-white py-10 border-b border-[#e5e7eb]">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <h2 className="mb-7 text-center text-xl font-bold text-[#1a1a2e]">Featured Companies</h2>

          <div className="flex items-center gap-3">
            {/* Left arrow */}
            <button
              type="button"
              onClick={() => scrollCompanies('left')}
              aria-label="Scroll left"
              className="shrink-0 flex h-9 w-9 items-center justify-center rounded-full border border-[#e0e0e0] bg-white shadow-sm text-[#666666] hover:border-[#7c3aed] hover:text-[#7c3aed] transition-colors"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>

            {/* Scrolling track */}
            <div
              className="flex-1 overflow-hidden"
              style={{
                maskImage: 'linear-gradient(to right, transparent 0%, black 6%, black 94%, transparent 100%)',
                WebkitMaskImage: 'linear-gradient(to right, transparent 0%, black 6%, black 94%, transparent 100%)',
              }}
            >
              <div
                ref={companyScrollRef}
                className="flex gap-5 overflow-x-auto"
                style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
              >
                {[...FEATURED_COMPANIES, ...FEATURED_COMPANIES].map((company, i) => (
                  <CompanyLogo key={`${company.name}-${i}`} company={company} />
                ))}
              </div>
            </div>

            {/* Right arrow */}
            <button
              type="button"
              onClick={() => scrollCompanies('right')}
              aria-label="Scroll right"
              className="shrink-0 flex h-9 w-9 items-center justify-center rounded-full border border-[#e0e0e0] bg-white shadow-sm text-[#666666] hover:border-[#7c3aed] hover:text-[#7c3aed] transition-colors"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
          </div>
        </div>
      </section>

      {/* ── POPULAR CATEGORIES ───────────────────────────────────────────── */}
      <section className="bg-white py-10 border-t border-[#e5e7eb]">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <h2 className="mb-6 text-xl font-bold text-[#1a1a2e]">Popular Categories</h2>
          <JobCategories />
        </div>
      </section>

      {/* ── TRENDING SKILLS + JOBS ───────────────────────────────────────── */}
      <section className="bg-white py-4 border-t border-[#e5e7eb]">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="rounded-xl border border-[#e5e7eb] bg-white px-4 py-3 shadow-sm flex flex-col gap-1">
            <HorizontalScrollRow label="Trending skills" items={TRENDING_SKILLS} />
            <div className="border-t border-[#f0f0f0]" />
            <HorizontalScrollRow label="Trending Jobs in India" items={TRENDING_JOBS} />
          </div>
        </div>
      </section>

      {/* ── FEATURED JOBS ────────────────────────────────────────────────── */}
      {(isLoading || featuredJobs.length > 0) && (
        <section className="bg-[#f5f5f5] py-10 border-t border-[#e5e7eb]">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="mb-6 flex items-center justify-between">
              <h2 className="text-xl font-bold text-[#1a1a2e]">Featured Jobs</h2>
              <Link to="/jobs" className="text-sm font-medium text-[#7c3aed] hover:underline">
                View all jobs &rsaquo;
              </Link>
            </div>
            {isLoading ? (
              <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
                {Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className="h-48 animate-pulse rounded-xl bg-gray-100" />
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
                {featuredJobs.map((job) => <JobCard key={job.id} job={job} />)}
              </div>
            )}
          </div>
        </section>
      )}

      {/* ── FIND JOB VACANCIES BY ────────────────────────────────────────── */}
      <section className="bg-[#f5f5f5] py-10 border-t border-[#e5e7eb]">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="rounded-xl border border-[#e5e7eb] bg-white p-6 shadow-sm">
            <h2 className="mb-5 text-lg font-bold text-[#1a1a2e]">Find job vacancies by</h2>

            <div className="flex gap-6 border-b border-[#e5e7eb] mb-5 overflow-x-auto" style={{ scrollbarWidth: 'none' }}>
              {VACANCY_TABS.map((tab) => (
                <button key={tab} type="button" onClick={() => setActiveTab(tab)}
                  className={`shrink-0 pb-3 text-sm font-medium transition-colors ${
                    activeTab === tab
                      ? 'border-b-2 border-[#7c3aed] text-[#7c3aed]'
                      : 'text-[#666666] hover:text-[#333333]'
                  }`}
                  style={activeTab === tab ? { marginBottom: '-1px' } : {}}>
                  {tab}
                </button>
              ))}
            </div>

            <div className="flex flex-wrap gap-2 mb-5">
              {VACANCY_DATA[activeTab].map((item) => (
                <Link key={item} to={`/jobs?q=${encodeURIComponent(item)}`}
                  className="rounded-full border border-[#e0e0e0] px-4 py-1.5 text-sm text-[#333333] hover:border-[#7c3aed] hover:text-[#7c3aed] transition-colors bg-white">
                  {item}
                </Link>
              ))}
            </div>

            <Link to="/jobs" className="text-sm font-medium text-[#7c3aed] hover:underline">
              View all jobs by {activeTab} &rsaquo;
            </Link>
          </div>
        </div>
      </section>

      {/* ── EMPTY STATE ──────────────────────────────────────────────────── */}
      {!isLoading && featuredJobs.length === 0 && (
        <section className="bg-white py-10 border-t border-[#e5e7eb]">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col items-center justify-center py-12">
              <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-purple-50">
                <Search className="h-7 w-7 text-[#7c3aed]" />
              </div>
              <p className="text-base font-medium text-[#333333]">No featured jobs at the moment</p>
              <p className="mt-1 text-sm text-[#666666]">Check back later or browse all jobs</p>
              <Link to="/jobs"
                className="mt-4 inline-flex items-center gap-2 rounded-lg bg-[#7c3aed] px-6 py-2.5 text-sm font-semibold text-white hover:opacity-90">
                Browse All Jobs
              </Link>
            </div>
          </div>
        </section>
      )}

      <Footer />
    </div>
  );
}
