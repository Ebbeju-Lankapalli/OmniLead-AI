import { postApi } from './client';
import {
  SearchRequest,
  SearchResponse,
  NaturalLanguageSearchRequest,
  ParsedSearchResponse,
} from '@/types/api';

export const searchApi = {
  search: (data: SearchRequest) =>
    postApi<SearchResponse>('/search', data),

  naturalLanguageSearch: (query: string, page = 1, pageSize = 20, forceRefresh = false) =>
    postApi<SearchResponse>('/search/natural-language', { query } as NaturalLanguageSearchRequest, {
      params: { page, page_size: pageSize, force_refresh: forceRefresh },
    }),

  parseNaturalLanguage: (query: string, forceRefresh = false) =>
    postApi<ParsedSearchResponse>('/search/natural-language/parse', { query } as NaturalLanguageSearchRequest, {
      params: { force_refresh: forceRefresh },
    }),
};
