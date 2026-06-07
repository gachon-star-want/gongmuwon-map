import bakeryIcon from '../../assets/bakery.png';
import beefBbqIcon from '../../assets/beef-bbq.png';
import bingsuIcon from '../../assets/bingsu.png';
import burgerIcon from '../../assets/burger.png';
import cafeIcon from '../../assets/cafe.png';
import chickenIcon from '../../assets/chicken.png';
import chineseIcon from '../../assets/chinese.png';
import dakgalbiIcon from '../../assets/dakgalbi.png';
import dessertIcon from '../../assets/dessert.png';
import donkatsuIcon from '../../assets/돈까스.png';
import gopchangIcon from '../../assets/gopchang.png';
import gukbapIcon from '../../assets/gukbap.png';
import indianIcon from '../../assets/indian.png';
import jokbalBossamIcon from '../../assets/jokbal-bossam.png';
import koreanNoodlesIcon from '../../assets/korean-noodles.png';
import koreanSetMealIcon from '../../assets/korean-set-meal.png';
import lunchBoxIcon from '../../assets/lunch-box.png';
import malatangIcon from '../../assets/malatang.png';
import mexicanIcon from '../../assets/mexican.png';
import pastaIcon from '../../assets/pasta.png';
import pizzaIcon from '../../assets/pizza.png';
import porkBbqIcon from '../../assets/pork-bbq.png';
import pubIcon from '../../assets/pub.png';
import ramenIcon from '../../assets/ramen.png';
import saladIcon from '../../assets/salad.png';
import sandwichIcon from '../../assets/sandwich.png';
import sashimiIcon from '../../assets/sashimi.png';
import agujjimIcon from '../../assets/아구찜.png';
import shabuShabuIcon from '../../assets/샤브샤브.png';
import sushiIcon from '../../assets/sushi.png';
import thaiIcon from '../../assets/thai.png';
import tteokbokkiIcon from '../../assets/tteokbokki.png';
import vietnameseIcon from '../../assets/vietnamese.png';
import jjukkumiIcon from '../../assets/쭈꾸미.png';
import type { Place } from './types';

export const FOOD_CATEGORIES = {
  'korean-set-meal': { label: 'Korean Set Meal', icon: koreanSetMealIcon },
  'shabu-shabu': { label: 'Shabu Shabu', icon: shabuShabuIcon },
  gukbap: { label: 'Gukbap', icon: gukbapIcon },
  'korean-noodles': { label: 'Korean Noodles', icon: koreanNoodlesIcon },
  dakgalbi: { label: 'Dakgalbi', icon: dakgalbiIcon },
  'jokbal-bossam': { label: 'Jokbal Bossam', icon: jokbalBossamIcon },
  gopchang: { label: 'Gopchang', icon: gopchangIcon },
  'pork-bbq': { label: 'Pork BBQ', icon: porkBbqIcon },
  'beef-bbq': { label: 'Beef BBQ', icon: beefBbqIcon },
  donkatsu: { label: 'Donkatsu', icon: donkatsuIcon },
  agujjim: { label: 'Agujjim', icon: agujjimIcon },
  jjukkumi: { label: 'Jjukkumi', icon: jjukkumiIcon },
  sashimi: { label: 'Sashimi', icon: sashimiIcon },
  sushi: { label: 'Sushi', icon: sushiIcon },
  ramen: { label: 'Ramen', icon: ramenIcon },
  chinese: { label: 'Chinese', icon: chineseIcon },
  malatang: { label: 'Malatang', icon: malatangIcon },
  tteokbokki: { label: 'Tteokbokki', icon: tteokbokkiIcon },
  chicken: { label: 'Chicken', icon: chickenIcon },
  pizza: { label: 'Pizza', icon: pizzaIcon },
  pasta: { label: 'Pasta', icon: pastaIcon },
  burger: { label: 'Burger', icon: burgerIcon },
  sandwich: { label: 'Sandwich', icon: sandwichIcon },
  salad: { label: 'Salad', icon: saladIcon },
  'lunch-box': { label: 'Lunch Box', icon: lunchBoxIcon },
  cafe: { label: 'Cafe', icon: cafeIcon },
  bakery: { label: 'Bakery', icon: bakeryIcon },
  dessert: { label: 'Dessert', icon: dessertIcon },
  bingsu: { label: 'Bingsu', icon: bingsuIcon },
  pub: { label: 'Pub', icon: pubIcon },
  vietnamese: { label: 'Vietnamese', icon: vietnameseIcon },
  thai: { label: 'Thai', icon: thaiIcon },
  indian: { label: 'Indian', icon: indianIcon },
  mexican: { label: 'Mexican', icon: mexicanIcon },
} as const;

export type FoodCategoryKey = keyof typeof FOOD_CATEGORIES;

export type FoodCategory = {
  key: FoodCategoryKey;
  label: (typeof FOOD_CATEGORIES)[FoodCategoryKey]['label'];
  icon: string;
};

const DEFAULT_CATEGORY: FoodCategoryKey = 'korean-set-meal';

const CATEGORY_KEYWORDS: Record<FoodCategoryKey, readonly string[]> = {
  'korean-set-meal': [
    '한식',
    '백반',
    '한정식',
    '가정식',
    '집밥',
    '찌개',
    '전골',
    '순두부',
    '김치',
    '제육',
    '오리',
    '보리밥',
  ],
  'shabu-shabu': [
    '샤브샤브',
    '샤부샤부',
    '샤브',
    '샤부',
    '월남쌈샤브',
    '밀푀유나베',
    '나베',
    'hotpot',
    'shabu',
  ],
  gukbap: ['국밥', '해장국', '설렁탕', '곰탕', '감자탕', '순대국', '순댓국', '탕국'],
  'korean-noodles': ['냉면', '국수', '칼국수', '막국수', '메밀', '우동', '수제비', '소바'],
  dakgalbi: ['닭갈비', '춘천닭갈비'],
  'jokbal-bossam': ['족발', '보쌈', '보족', '장충동'],
  gopchang: ['곱창', '막창', '대창', '양대창'],
  'pork-bbq': ['삼겹살', '돼지고기', '돼지', '목살', '갈매기살', '오겹살', '돈육'],
  'beef-bbq': ['소고기', '소갈비', '한우', '육회', '등심', '불고기', '갈비살', '차돌'],
  donkatsu: ['돈까스', '돈가스', '돈카츠', '돈카스', '카츠', '가츠', '가스', '커틀릿', '커틀렛', 'cutlet', 'katsu', 'tonkatsu'],
  agujjim: [
    '아구찜',
    '아귀찜',
    '아구탕',
    '아귀탕',
    '해물찜',
    '해물탕',
    '생선찜',
    '생선탕',
    '대구뽈찜',
    '대구탕',
    '동태탕',
    '알탕',
    '매운탕',
    '꽃게찜',
    '꽃게탕',
    '조개찜',
  ],
  jjukkumi: ['쭈꾸미', '주꾸미', '쭈꾸미볶음', '주꾸미볶음', '낙지', '낙지볶음', '오징어', '오징어볶음', '문어', '문어숙회'],
  sashimi: [' 회', '>회', '생선회', '횟집', '수산', '참치', '광어', '우럭', '연어', '해산물', '해물'],
  sushi: ['초밥', '스시', 'sushi'],
  ramen: ['라멘', '라면', 'ramen'],
  chinese: ['중식', '중국', '짜장', '자장', '짬뽕', '탕수육', '양꼬치', '딤섬'],
  malatang: ['마라', '마라탕', '마라샹궈', '훠궈'],
  tteokbokki: ['분식', '떡볶이', '튀김', '순대', '김밥', '어묵', '토스트'],
  chicken: ['치킨', '닭강정', '후라이드', '양념치킨', '통닭', '닭'],
  pizza: ['피자', 'pizza'],
  pasta: ['양식', '파스타', '이탈리안', '이탈리아', '스테이크', '리조또', '필라프'],
  burger: ['햄버거', '버거', 'burger'],
  sandwich: ['샌드위치', '샌드위치전문', 'sandwich'],
  salad: ['샐러드', '포케', 'poke'],
  'lunch-box': ['도시락', '덮밥', '벤또', 'bento'],
  cafe: ['카페', '커피', 'coffee', 'espresso', '브런치', 'tea', '티'],
  bakery: ['빵', '베이커리', '제과', '제빵', 'bakery', '뚜레쥬르', '파리바게뜨'],
  dessert: ['디저트', '케이크', '마카롱', '와플', '아이스크림', '도넛', '쿠키', '초콜릿'],
  bingsu: ['빙수', '설빙'],
  pub: ['술집', '호프', '맥주', '주점', '포차', '이자카야', 'bar', 'pub'],
  vietnamese: ['베트남', '쌀국수', '월남쌈', '반미', 'pho', 'vietnam'],
  thai: ['태국', '타이', '팟타이', '똠얌', '쏨땀', 'thai'],
  indian: ['인도', '커리', '카레', '탄두리', '난', '마살라', 'india'],
  mexican: ['멕시칸', '멕시코', '타코', '부리또', '퀘사디아', '나초', 'mexican'],
};

const PRIORITY: readonly FoodCategoryKey[] = [
  'malatang',
  'shabu-shabu',
  'sushi',
  'ramen',
  'bingsu',
  'donkatsu',
  'agujjim',
  'jjukkumi',
  'dakgalbi',
  'jokbal-bossam',
  'gopchang',
  'beef-bbq',
  'pork-bbq',
  'sashimi',
  'tteokbokki',
  'chicken',
  'pizza',
  'pasta',
  'burger',
  'sandwich',
  'salad',
  'lunch-box',
  'bakery',
  'dessert',
  'cafe',
  'vietnamese',
  'thai',
  'indian',
  'mexican',
  'chinese',
  'gukbap',
  'korean-noodles',
  'pub',
  'korean-set-meal',
];

function textForClassification(place: Pick<Place, 'name' | 'category' | 'menu_items'>) {
  return [
    place.name,
    place.category,
    ...(place.menu_items ?? []),
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase();
}

export function classifyFoodCategory(place: Pick<Place, 'name' | 'category' | 'menu_items'>): FoodCategory {
  const text = textForClassification(place);
  let bestKey: FoodCategoryKey = DEFAULT_CATEGORY;
  let bestScore = 0;

  for (const key of PRIORITY) {
    const score = CATEGORY_KEYWORDS[key].reduce((total, keyword) => {
      return total + (text.includes(keyword.toLowerCase()) ? 1 : 0);
    }, 0);
    if (score > bestScore) {
      bestKey = key;
      bestScore = score;
    }
  }

  return {
    key: bestKey,
    label: FOOD_CATEGORIES[bestKey].label,
    icon: FOOD_CATEGORIES[bestKey].icon,
  };
}
