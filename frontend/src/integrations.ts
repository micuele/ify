export type TmdbMovie = {
  id: number;
  title: string;
  original_title: string;
  overview: string;
  release_date: string | null;
  runtime_minutes: number | null;
  genres: Array<{ id: number; name: string }>;
  original_language: string;
  popularity: number;
  vote_average: number;
  vote_count: number;
  poster_path: string | null;
  poster_url: string | null;
  backdrop_path: string | null;
  backdrop_url: string | null;
  tmdb_url: string | null;
};

export type LetterboxdFilm = {
  title: string;
  year: number | null;
  watched_date: string | null;
  published_at: string | null;
  rating: number | null;
  liked: boolean;
  rewatch: boolean;
  letterboxd_url: string;
  letterboxd_guid: string;
  letterboxd_poster_url: string | null;
  tmdb_id: number | null;
  tmdb: {
    status: 'matched' | 'unavailable';
    match_method: 'id' | 'title_year' | null;
    movie: TmdbMovie | null;
    error?: string;
  };
};

export type MediaSlot<T> = {
  slot: number;
  key: string;
  image_key: string;
  source: string;
  data: T | null;
};

export type VibeOutput = {
  slot: number;
  key: string;
  image_key: string;
  label: string;
  description: string;
  match_score: number;
  confidence: number;
  evidence: string[];
};

export type LetterboxdIntegration = {
  provider: 'letterboxd';
  username: string;
  profile_url: string;
  generated_at: string;
  slot_count: number;
  film_count: number;
  selected_output: VibeOutput;
  slots: Array<MediaSlot<LetterboxdFilm>>;
};

export async function getLetterboxdFilms(
  username: string,
  limit = 24,
): Promise<LetterboxdIntegration> {
  const params = new URLSearchParams({
    username,
    limit: String(limit),
  });
  const response = await fetch(`/api/integrations/letterboxd?${params}`, {
    credentials: 'include',
  });
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data?.error || `Request failed with ${response.status}`);
  }

  return data as LetterboxdIntegration;
}
