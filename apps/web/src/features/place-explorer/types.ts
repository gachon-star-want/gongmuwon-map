export type Grade = '★★★' | '★★' | '★' | '✦';

export type SortMode = 'score' | 'recent' | 'visits';

export type Place = {
  id: string;
  name: string;
  road_address: string | null;
  road_address_part: string | null;
  latitude: number | null;
  longitude: number | null;
  category: string | null;
  is_closed: boolean;
  closure_report_count: number;
  score: number;
  grade: Grade;
  last_visit_at: string | null;
  visit_count_12m: number | null;
  unique_department_count_12m: number | null;
  unique_agency_count_12m?: number | null;
  avg_amount_per_person?: number | null;
  matched_fields?: string[];
  photo_url?: string | null;
  menu_items?: string[] | null;
};

export type Visit = {
  id: string;
  visit_date: string;
  amount: number;
  party_size: number | null;
  department_name: string | null;
  rank_label: string | null;
  representative: string | null;
  purpose: string | null;
  source_url: string | null;
  source_title: string | null;
};

export type PlaceReactionSummary = {
  like_count: number;
  dislike_count: number;
  user_reaction: 'like' | 'dislike' | null;
};

export type Region = {
  region: string;
  label: string;
  place_count: number;
  top_place_count: number;
  recommended_place_count: number;
  new_place_count: number;
  center: { latitude: number; longitude: number };
  bbox: {
    min_latitude: number;
    min_longitude: number;
    max_latitude: number;
    max_longitude: number;
  };
  last_visit_at: string | null;
};

export type SearchResponse = {
  items: Place[];
  next_cursor: string | null;
  source_notice: string;
};

export type RegionsResponse = {
  items: Region[];
  source_notice: string;
};
