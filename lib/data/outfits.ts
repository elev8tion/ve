// Extracted from chunk_6935-fbee254de2f4026a.js — module 8426
// Real outfit catalog: 43 tops, 42 bottoms, 40 shoes, 21 hats
// Descriptions are sent verbatim as customOutfitDescription to /api/clips/generate

const SUPABASE_URL = 'https://lugfcahmpvajonmzhqcd.supabase.co';

export type OutfitCategory = 'tops' | 'bottoms' | 'shoes' | 'hats';

export interface OutfitItem {
  id: string;
  category: OutfitCategory;
  label: string;
  description: string;
  imageUrl: string;
}

export interface OutfitSelection {
  tops?: string;
  bottoms?: string;
  shoes?: string;
  hats?: string;
}

export interface OutfitPreset {
  id: string;
  label: string;
  items: OutfitSelection;
}

function item(id: string, category: OutfitCategory, label: string, description: string): OutfitItem {
  return {
    id, category, label, description,
    imageUrl: `${SUPABASE_URL}/storage/v1/object/public/outfits/${category}/${id}.png`,
  };
}

export function getOutfitThumbnailUrl(category: OutfitCategory, id: string): string {
  return `${SUPABASE_URL}/storage/v1/render/image/public/outfits/${category}/${id}.png?width=200&height=200&resize=cover&quality=75`;
}

export const ALL_ITEMS: OutfitItem[] = [
  // TOPS (43)
  item('casual_black_tee', 'tops', 'Black Tee', 'plain black crew-neck t-shirt'),
  item('fit0_top', 'tops', 'Burgundy Bomber', 'oxblood dark burgundy-brown leather bomber jacket with shirt-style collar and gold zipper, worn over a crisp white dress shirt with burgundy and tan diagonal stripe necktie'),
  item('fit1_top', 'tops', 'Striped Polo', 'oversized red and white horizontal-striped short-sleeve polo shirt with layered gold chain necklace'),
  item('fit2_top', 'tops', 'Grey V-Neck', 'charcoal grey V-neck pullover sweater over a white collared button-up shirt with collar popped'),
  item('fit3_top', 'tops', 'UNC Crewneck', 'navy blue oversized Carolina Tar Heels collegiate crewneck sweatshirt'),
  item('fit4_top', 'tops', 'Check Button-Up', 'oversized grey and navy micro-check short-sleeve button-up shirt over a white long-sleeve thermal undershirt'),
  item('fit5_top', 'tops', 'Leather Bomber', 'dark burgundy-brown leather zip-up bomber jacket over a white button-up shirt'),
  item('fit6_top', 'tops', 'Gingham Shirt', 'olive brown gingham plaid cropped short-sleeve button-up worn open over a white tee'),
  item('fit7_top', 'tops', 'Washed Denim Jacket', 'oversized cropped washed-black denim jacket over a dark graphite crewneck sweatshirt'),
  item('fit8_top', 'tops', 'Striped Button-Up', 'oversized short-sleeve light-blue-and-white vertical-striped button-up shirt'),
  item('fit9_top', 'tops', 'Camo Hoodie', 'faded grey-and-tan camo cropped zip-up hoodie over a white tee'),
  item('fit10_top', 'tops', 'Union Jack Tee', 'royal-blue long-sleeve tee with Union Jack flag and crucifix graphic'),
  item('fit11_top', 'tops', 'Red Bouclé Jacket', 'cropped red bouclé-wool zip-up jacket over a light-blue collared shirt'),
  item('fit12_top', 'tops', 'SS Card Tee', 'oversized white tee with Social Security card graphic patch on chest'),
  item('fit13_top', 'tops', 'Indigo Trucker', 'dark indigo cropped denim trucker jacket with chest flap pockets'),
  item('fit14_top', 'tops', 'Black Leather Trucker', 'black leather snap-button trucker jacket worn open over a white tee'),
  item('fit15_top', 'tops', 'Plaid Flannel', 'oversized red-cream-and-yellow color-blocked plaid flannel button-up'),
  item('fit16_top', 'tops', 'Denim + Hoodie', 'washed-black denim trucker jacket over a grey zip-up hoodie'),
  item('fit17_top', 'tops', 'Grey Henley', 'heather-grey crewneck sweatshirt with small henley button placket'),
  item('fit18_top', 'tops', 'Pink Bomber', 'cropped dusty-pink padded bomber jacket with gold zip over a white tee'),
  item('fit19_top', 'tops', 'Vintage Jersey', 'oversized cropped green vintage-wash athletic jersey tee with number graphics'),
  item('fit20_top', 'tops', 'Rugby Polo', 'oversized yellow-and-light-blue wide-stripe long-sleeve rugby polo shirt'),
  item('fit21_top', 'tops', 'Black V-Neck Sweater', 'black fine-knit V-neck sweater over a white dress shirt with tie'),
  item('fit22_top', 'tops', 'Panther Graphic Tee', 'oversized cream-white vintage graphic tee with painted woman and panther image'),
  item('fit23_top', 'tops', 'Black Zip Hoodie', 'black full-zip cotton hoodie over a white crewneck tee, small logo'),
  item('fit24_top', 'tops', 'Quarter-Zip Rugby', 'oversized navy-and-light-blue bold-stripe quarter-zip rugby pullover'),
  item('fit25_top', 'tops', 'Polo Sweater', 'white cotton crewneck Polo Ralph Lauren sweater with small navy logo'),
  item('fit26_top', 'tops', 'Tan Bomber', 'khaki-tan multi-pocket cropped bomber jacket over a grey zip hoodie'),
  item('fit27_top', 'tops', 'Grey Wool Zip', 'cropped grey wool zip-up jacket with dual chest flap pockets'),
  item('fit28_top', 'tops', 'Brown Hoodie + Tie', 'oversized brown zip-up hoodie over a white dress shirt with tie'),
  item('fit29_top', 'tops', 'Football Jersey', 'black oversized short-sleeve football jersey with white 55 graphic'),
  item('fit30_top', 'tops', 'Brown Trucker', 'cropped washed brown denim trucker jacket over a black zip-up hoodie'),
  item('fit31_top', 'tops', 'Eagle Graphic Tee', 'oversized black short-sleeve tee with large grey eagle graphic'),
  item('fit32_top', 'tops', 'Olive Fleece Polo', 'oversized olive-green fleece polo pullover with three-button placket'),
  item('fit33_top', 'tops', 'Indigo Work Jacket', 'dark indigo cropped zip-up work jacket with white contrast stitching'),
  item('fit34_top', 'tops', 'Gingham + Tie', 'red-and-white gingham short-sleeve button-up over a white long-sleeve with tie'),
  item('fit35_top', 'tops', 'Steel Blue Hoodie', 'matching steel-blue heavyweight oversized hoodie with cream embroidery'),
  item('fit36_top', 'tops', 'Cream Trucker', 'cream-beige denim trucker jacket with brown buttons and chest pockets'),
  item('fit37_top', 'tops', 'CONAN Bomber', 'black nylon bomber jacket with CONAN white embroidery on chest'),
  item('fit38_top', 'tops', 'Brown Work Jacket', 'brown cotton work jacket with flap pockets over a white dress shirt'),
  item('fit39_top', 'tops', 'Mustard Tee', 'oversized mustard-yellow tee with EVERYTHING embroidered text'),
  item('fit40_top', 'tops', 'Pink Hoodie', 'oversized bubblegum-pink cropped hoodie with tonal embroidery'),
  item('fit41_top', 'tops', 'Plaid Shacket', 'open brown-and-cream plaid flannel shirt jacket over a white tee'),

  // BOTTOMS (42)
  item('fit0_btm', 'bottoms', 'Wide-Leg Dark Jeans', 'heavily faded and whiskered dark indigo ultra-wide-leg baggy jeans'),
  item('fit1_btm', 'bottoms', 'Camo Shorts', 'green camouflage cargo shorts hitting below the knee'),
  item('fit2_btm', 'bottoms', 'Grey Sweats', 'light heather grey wide-leg sweatpants'),
  item('fit3_btm', 'bottoms', 'Light Denim Shorts', 'baggy light-wash denim shorts hitting below the knee'),
  item('fit4_btm', 'bottoms', 'Raw Denim', 'dark indigo straight-leg raw denim jeans'),
  item('fit5_btm', 'bottoms', 'Faded Wide-Leg Jeans', 'heavily faded dark wash ultra-wide-leg baggy denim jeans'),
  item('fit6_btm', 'bottoms', 'Drawstring Baggy Jeans', 'ultra-wide-leg light wash baggy denim jeans with drawstring waist'),
  item('fit7_btm', 'bottoms', 'Black Baggy Jeans', 'black baggy wide-leg denim jeans'),
  item('fit8_btm', 'bottoms', 'Indigo Baggy Jeans', 'dark indigo baggy wide-leg denim jeans'),
  item('fit9_btm', 'bottoms', 'Black Jeans + Chain', 'washed-black super-wide-leg baggy jeans with silver wallet chain'),
  item('fit10_btm', 'bottoms', 'Woodland Cargo Shorts', 'green and brown woodland-camo oversized cargo shorts'),
  item('fit11_btm', 'bottoms', 'Studded Black Jeans', 'faded black super-wide-leg baggy jeans with studded belt and chain'),
  item('fit12_btm', 'bottoms', 'Text Denim Shorts', 'light-wash denim baggy shorts with bold text across the front'),
  item('fit13_btm', 'bottoms', 'Medium Wash Jeans', 'medium-wash faded loose-fit straight-leg jeans with brown leather belt'),
  item('fit14_btm', 'bottoms', 'Washed Black Jeans', 'faded washed-black baggy straight-leg jeans'),
  item('fit15_btm', 'bottoms', 'Ripped Wide Jeans', 'light-wash baggy wide-leg jeans with blown-out knee rips'),
  item('fit16_btm', 'bottoms', 'Faded Black Wide', 'faded black super-wide-leg baggy jeans'),
  item('fit17_btm', 'bottoms', 'Drawstring Light Jeans', 'light-wash baggy straight-leg jeans with drawstring waist'),
  item('fit18_btm', 'bottoms', 'Camo Cargo Pants', 'green-brown woodland camo extra-wide-leg cargo pants with black belt'),
  item('fit19_btm', 'bottoms', 'Beige Cargo Pants', 'dirty-wash beige denim cargo pants with large flap pockets and chain'),
  item('fit20_btm', 'bottoms', 'Graphic Jeans', 'light-wash baggy graphic-print jeans with studded leather belt'),
  item('fit21_btm', 'bottoms', 'Charcoal Baggy Jeans', 'washed charcoal-grey wide-leg baggy jeans with frayed hems'),
  item('fit22_btm', 'bottoms', 'Black Nylon Shorts', 'black nylon knee-length athletic shorts with small logo'),
  item('fit23_btm', 'bottoms', 'Light Baggy Jeans', 'light-wash baggy straight-leg jeans'),
  item('fit24_btm', 'bottoms', 'Light Straight Jeans', 'light-wash loose-fit straight-leg jeans'),
  item('fit25_btm', 'bottoms', 'Super-Baggy Jeans', 'light-wash super-baggy straight-leg jeans, silver keychain and chain'),
  item('fit26_btm', 'bottoms', 'Olive Baggy Jeans', 'olive dirty-wash baggy jeans with brown leather belt'),
  item('fit27_btm', 'bottoms', 'Grey Straight Jeans', 'faded grey loose-fit straight-leg jeans'),
  item('fit28_btm', 'bottoms', 'Brown Work Jeans', 'baggy dark brown cuffed workwear jeans with oversized silver buckle belt'),
  item('fit29_btm', 'bottoms', 'Dark Grey Wide Jeans', 'extra-wide-leg faded dark grey baggy jeans'),
  item('fit30_btm', 'bottoms', 'Baggy Blue Jeans', 'super-baggy light-wash blue jeans with silver chain clip'),
  item('fit31_btm', 'bottoms', 'Grey Cargos', 'relaxed-fit grey cargo pants with multiple pockets'),
  item('fit32_btm', 'bottoms', 'Brown Canvas Pants', 'baggy faded brown double-knee canvas work pants'),
  item('fit33_btm', 'bottoms', 'Indigo Wide Chain', 'matching extra-wide-leg dark indigo jeans with silver ball-chain'),
  item('fit34_btm', 'bottoms', 'Light Jeans + Keychain', 'super-baggy light-wash blue jeans with silver keychain clip'),
  item('fit35_btm', 'bottoms', 'Steel Blue Sweats', 'matching steel-blue wide-leg drawstring sweatpants with plain hem'),
  item('fit36_btm', 'bottoms', 'Slim Straight Jeans', 'light-wash blue slim-straight jeans'),
  item('fit37_btm', 'bottoms', 'Baggy Wide Jeans', 'light-wash baggy wide-leg jeans'),
  item('fit38_btm', 'bottoms', 'Black Belt Jeans', 'faded black ultra-wide-leg baggy jeans with black leather belt'),
  item('fit39_btm', 'bottoms', 'Indigo Shorts', 'dark indigo ultra-wide-leg denim shorts below the knee with chain'),
  item('fit40_btm', 'bottoms', 'Cream Cargo Pants', 'cream off-white ultra-wide-leg drawstring cargo pants with large pockets'),
  item('fit41_btm', 'bottoms', 'Charcoal Straight Jeans', 'faded charcoal-gray straight-leg baggy jeans'),

  // SHOES (40)
  item('fit0_shoe', 'shoes', 'White Court Sneakers', "men's white leather low-top court sneakers, clean minimal design"),
  item('fit1_shoe', 'shoes', 'Jordan 1 Red', 'red and white Nike Air Jordan 1 high-top sneakers with white laces'),
  item('fit2_shoe', 'shoes', 'Retro Runners', 'white and blue retro low-profile running sneakers'),
  item('fit3_shoe', 'shoes', 'NB Chunky', 'grey and cream New Balance chunky low-top sneakers'),
  item('fit4_shoe', 'shoes', 'Brown Dress Shoes', 'dark brown leather lace-up dress shoes'),
  item('fit5_shoe', 'shoes', 'White Low-Tops', 'white leather low-top sneakers, clean minimal design'),
  item('fit6_shoe', 'shoes', 'Suede Chelseas', 'tan suede chelsea boots with stacked heel'),
  item('fit7_shoe', 'shoes', 'Old Skools', 'black-and-white low-top Vans Old Skool sneakers'),
  item('fit9_shoe', 'shoes', 'Suede Lug Boots', 'tan suede lug-sole boots'),
  item('fit10_shoe', 'shoes', 'Black Chunky Sneakers', 'all-black chunky sneakers with white crew socks'),
  item('fit11_shoe', 'shoes', 'Chunky Loafers', 'black chunky leather loafers'),
  item('fit12_shoe', 'shoes', 'Silver Runners', 'silver metallic chunky running sneakers'),
  item('fit13_shoe', 'shoes', 'Brown Pointed Boots', 'dark brown leather pointed-toe boots'),
  item('fit14_shoe', 'shoes', 'White Chunky Sneakers', 'all-white chunky low-top leather sneakers'),
  item('fit15_shoe', 'shoes', 'Jordan 1 Low', 'red-and-white low-top Jordan 1 sneakers'),
  item('fit16_shoe', 'shoes', 'Tan Round Boots', 'tan suede round-toe boots'),
  item('fit17_shoe', 'shoes', 'Chucks', 'black-and-white low-top Converse Chuck Taylor sneakers'),
  item('fit18_shoe', 'shoes', 'Timberlands', 'wheat-tan Timberland lug-sole boots'),
  item('fit19_shoe', 'shoes', 'Wheat Timbs', 'wheat Timberland work boots'),
  item('fit20_shoe', 'shoes', 'Embellished Boots', 'embellished chunky boots'),
  item('fit21_shoe', 'shoes', 'Black Loafers', 'black chunky leather loafers'),
  item('fit22_shoe', 'shoes', 'Balenciaga Runners', 'silver-and-white Balenciaga-style chunky runner sneakers'),
  item('fit23_shoe', 'shoes', 'Adidas Sambas', 'white Adidas Samba sneakers with light-blue side stripes'),
  item('fit24_shoe', 'shoes', 'Tan Mules', 'tan suede slip-on mules'),
  item('fit25_shoe', 'shoes', 'AF1s', 'white Nike Air Force 1 Low sneakers'),
  item('fit26_shoe', 'shoes', 'Retro Sneakers', 'white-and-grey retro running sneakers'),
  item('fit27_shoe', 'shoes', 'BW Leather Sneakers', 'black-and-white low-top leather sneakers'),
  item('fit28_shoe', 'shoes', 'Low-Cut Boots', 'tan suede round-toe low-top boots'),
  item('fit29_shoe', 'shoes', 'Suede Low Boots', 'tan suede low-cut boots'),
  item('fit30_shoe', 'shoes', 'Tan Boots', 'tan suede round-toe boots'),
  item('fit31_shoe', 'shoes', 'Canvas Slip-Ons', 'black canvas slip-on sneakers with white rubber toe caps'),
  item('fit33_shoe', 'shoes', 'Chunky Sole Boots', 'tan suede chunky-sole boots'),
  item('fit34_shoe', 'shoes', 'Mule Boots', 'tan suede mule-style boots'),
  item('fit35_shoe', 'shoes', 'White Court Low', 'white low-top leather court sneakers'),
  item('fit36_shoe', 'shoes', 'Court + Aviators', 'white leather low-top court sneakers with gold-tinted round sunglasses'),
  item('fit37_shoe', 'shoes', 'Moc-Toe Shoes', 'tan wheat suede low-top moc-toe shoes with chunky gum sole'),
  item('fit38_shoe', 'shoes', 'Wheat Low Boots', 'wheat tan suede low-top boots'),
  item('fit39_shoe', 'shoes', 'Timb 6-Inch', 'wheat nubuck Timberland 6-inch lace-up boots with white crew socks'),
  item('fit40_shoe', 'shoes', 'Low Profile Boots', 'tan wheat suede low-profile boots'),
  item('fit41_shoe', 'shoes', 'Mustard Slip-Ons', 'mustard-tan suede low-top slip-on shoes'),

  // HATS (21)
  item('fit0_hat', 'hats', 'GG Monogram Cap', 'beige tan canvas five-panel cap with all-over GG monogram print in taupe, adjustable closure'),
  item('fit1_hat', 'hats', 'Red Snapback', 'red snapback cap worn backwards with white embroidered text'),
  item('fit4_hat', 'hats', 'Navy Snapback', 'navy blue snapback baseball cap with white embroidered letter'),
  item('fit5_hat', 'hats', 'Monogram Cap', 'beige monogram-print five-panel cap'),
  item('fit7_hat', 'hats', 'Camo NY Cap', 'camo-print fitted cap with orange NY logo'),
  item('fit8_hat', 'hats', 'Yankees Fitted', 'black New York Yankees fitted cap'),
  item('fit11_hat', 'hats', 'Dodgers Fitted', 'black LA Dodgers fitted cap'),
  item('fit15_hat', 'hats', 'Vintage Trucker', 'brown distressed vintage trucker cap'),
  item('fit16_hat', 'hats', 'LA Fitted', 'black LA Dodgers fitted cap'),
  item('fit20_hat', 'hats', 'Yellow Sox Cap', 'yellow Chicago White Sox fitted cap'),
  item('fit24_hat', 'hats', 'Black Dodgers', 'black LA Dodgers fitted cap'),
  item('fit27_hat', 'hats', 'Beige Dad Cap', 'beige embroidered baseball cap'),
  item('fit29_hat', 'hats', 'Backwards Fitted', 'black fitted baseball cap worn backwards'),
  item('fit30_hat', 'hats', 'NY Fitted', 'black New York Yankees fitted cap'),
  item('fit31_hat', 'hats', 'Grey Snapback', 'dark grey snapback cap with pink underbrim'),
  item('fit33_hat', 'hats', 'Sbl Studios Cap', 'black embroidered Sbl Studios snapback cap'),
  item('fit34_hat', 'hats', 'Yankees Black', 'black New York Yankees fitted cap'),
  item('fit38_hat', 'hats', 'Yankees Classic', 'black New York Yankees fitted cap'),
  item('fit39_hat', 'hats', 'Khaki + Shades', 'khaki tan five-panel cap with black sunglasses'),
  item('fit40_hat', 'hats', 'Pink Durag', 'pink durag headwrap'),
  item('fit41_hat', 'hats', 'Mustard Fitted', 'mustard-yellow New Era fitted cap with red underbrim'),
];

const ITEM_MAP = new Map(ALL_ITEMS.map((i) => [i.id, i]));

export function getOutfitItem(id: string): OutfitItem | undefined {
  return ITEM_MAP.get(id);
}

export function getItemsByCategory(category: OutfitCategory): OutfitItem[] {
  return ALL_ITEMS.filter((i) => i.category === category);
}

export const TOPS = getItemsByCategory('tops');
export const BOTTOMS = getItemsByCategory('bottoms');
export const SHOES = getItemsByCategory('shoes');
export const HATS = getItemsByCategory('hats');

// Joins selected item descriptions into the prompt string sent to Kling AI
export function buildOutfitDescription(selection: OutfitSelection): string {
  const parts: string[] = [];
  if (selection.tops) {
    const i = ITEM_MAP.get(selection.tops);
    if (i) parts.push(`Top: ${i.description}`);
  }
  if (selection.bottoms) {
    const i = ITEM_MAP.get(selection.bottoms);
    if (i) parts.push(`Bottom: ${i.description}`);
  }
  if (selection.shoes) {
    const i = ITEM_MAP.get(selection.shoes);
    if (i) parts.push(`Shoes: ${i.description}`);
  }
  if (selection.hats) {
    const i = ITEM_MAP.get(selection.hats);
    if (i) parts.push(`Hat: ${i.description}`);
  }
  return parts.join('. ') + '.';
}

export const OUTFIT_PRESETS: OutfitPreset[] = [
  { id: 'casual', label: 'Casual', items: { tops: 'casual_black_tee', bottoms: 'fit2_btm', shoes: 'fit25_shoe' } },
  { id: 'formal', label: 'Formal', items: { tops: 'fit2_top', bottoms: 'fit36_btm', shoes: 'fit4_shoe' } },
  { id: 'streetwear', label: 'Streetwear', items: { tops: 'fit9_top', bottoms: 'fit38_btm', shoes: 'fit9_shoe' } },
];

export const OUTFIT_CATEGORIES: OutfitCategory[] = ['tops', 'bottoms', 'shoes', 'hats'];
