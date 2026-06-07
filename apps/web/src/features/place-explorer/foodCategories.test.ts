import { describe, expect, it } from 'vitest';
import { FOOD_CATEGORIES, classifyFoodCategory } from './foodCategories';

describe('food category classification', () => {
  it('keeps the food category taxonomy fixed to English keys and labels', () => {
    const entries = Object.entries(FOOD_CATEGORIES);

    expect(entries).toHaveLength(34);
    expect(entries.map(([key]) => key)).toEqual([
      'korean-set-meal',
      'shabu-shabu',
      'gukbap',
      'korean-noodles',
      'dakgalbi',
      'jokbal-bossam',
      'gopchang',
      'pork-bbq',
      'beef-bbq',
      'donkatsu',
      'agujjim',
      'jjukkumi',
      'sashimi',
      'sushi',
      'ramen',
      'chinese',
      'malatang',
      'tteokbokki',
      'chicken',
      'pizza',
      'pasta',
      'burger',
      'sandwich',
      'salad',
      'lunch-box',
      'cafe',
      'bakery',
      'dessert',
      'bingsu',
      'pub',
      'vietnamese',
      'thai',
      'indian',
      'mexican',
    ]);
    for (const [, category] of entries) {
      expect(category.label).toMatch(/^[A-Za-z ]+$/);
      expect(category.icon).toMatch(/\.png/);
    }
  });

  it('maps known Korean restaurant signals to one of the fixed English categories', () => {
    const cases = [
      ['창고43', '음식점 > 한식 > 한우', 'beef-bbq'],
      ['을밀대', '음식점 > 한식 > 냉면', 'korean-noodles'],
      ['마라공방', '음식점 > 중식 > 마라탕', 'malatang'],
      ['스시소라', '음식점 > 일식 > 초밥', 'sushi'],
      ['스타벅스', '음식점 > 카페 > 커피전문점', 'cafe'],
      ['반미362', '음식점 > 아시아음식 > 베트남음식', 'vietnamese'],
      ['정성본샤브수끼', '음식점 > 한식 > 샤브샤브', 'shabu-shabu'],
      ['홍익돈까스', '음식점 > 일식 > 돈까스', 'donkatsu'],
      ['쭈꾸미도사', '음식점 > 한식 > 쭈꾸미', 'jjukkumi'],
      ['마산아구찜', '음식점 > 한식 > 아구찜', 'agujjim'],
    ] as const;

    for (const [name, category, expected] of cases) {
      expect(classifyFoodCategory({ name, category, menu_items: null }).key).toBe(expected);
    }
  });

  it('falls back to an existing category instead of creating an unknown category', () => {
    const category = classifyFoodCategory({
      name: '알 수 없는 식당',
      category: '음식점 > 기타',
      menu_items: null,
    });

    expect(category.key).toBe('korean-set-meal');
    expect(category.key in FOOD_CATEGORIES).toBe(true);
  });

  it('maps similar Korean dishes to the closest specific food icon', () => {
    const cases = [
      ['등촌샤브칼국수', '음식점 > 한식 > 칼국수', ['버섯샤브샤브'], 'shabu-shabu'],
      ['밀푀유나베 전문점', '음식점 > 일식 > 나베', null, 'shabu-shabu'],
      ['카츠바이콘반', '음식점 > 일식', ['로스카츠', '히레카츠'], 'donkatsu'],
      ['포크커틀릿하우스', '음식점 > 양식', ['커틀릿'], 'donkatsu'],
      ['낙지한마당', '음식점 > 한식', ['낙지볶음'], 'jjukkumi'],
      ['오징어세상', '음식점 > 한식', ['오징어볶음'], 'jjukkumi'],
      ['부산해물찜', '음식점 > 한식', ['꽃게찜'], 'agujjim'],
      ['속초매운탕', '음식점 > 한식', ['생선탕'], 'agujjim'],
    ] as const;

    for (const [name, category, menuItems, expected] of cases) {
      expect(classifyFoodCategory({ name, category, menu_items: menuItems }).key).toBe(expected);
    }
  });
});
